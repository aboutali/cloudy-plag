"""Embedding-based paraphrase / translation detector.

Computes multilingual sentence embeddings for document and source spans,
then uses pgvector cosine search to find candidates whose semantic similarity
to a document span exceeds a threshold but whose surface-level n-gram overlap
is below it (otherwise the n-gram detector already caught it).

Findings are emitted with kind=paraphrase and require two reviewer confirms
to become `documented` (see docs/evidence-model.md).
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.detectors.ngram import MIN_SPAN_CHARS, fingerprint, jaccard
from app.embeddings import embed
from app.models import (
    AnalysisRun,
    Document,
    DocumentSpan,
    Finding,
    SourceSpan,
)

DETECTOR_ID = "embedding_paraphrase"
DETECTOR_VERSION = "0.1.0"

SIM_THRESHOLD = 0.78  # cosine similarity floor
NGRAM_OVERLAP_MAX = 0.20  # only emit if n-gram overlap is *below* this (else n-gram caught it)
TOP_K = 5  # nearest source spans per document span


def _ensure_embeddings(session: Session, spans: list, label: str) -> None:
    missing = [s for s in spans if s.embedding is None and len(s.text) >= MIN_SPAN_CHARS]
    if not missing:
        return
    vectors = embed([s.text for s in missing])
    for s, v in zip(missing, vectors, strict=True):
        s.embedding = v.tolist()
    session.flush()


def run_detector(
    session: Session,
    document_id: uuid.UUID,
    source_ids: Iterable[uuid.UUID] | None = None,
) -> tuple[uuid.UUID, int]:
    document = session.get(Document, document_id)
    if document is None:
        raise ValueError(f"Document {document_id} not found")

    doc_spans = [
        s
        for s in session.scalars(
            select(DocumentSpan).where(DocumentSpan.document_id == document_id)
        ).all()
        if len(s.text) >= MIN_SPAN_CHARS
    ]
    _ensure_embeddings(session, doc_spans, "doc")

    src_stmt = select(SourceSpan)
    if source_ids is not None:
        src_stmt = src_stmt.where(SourceSpan.source_id.in_(list(source_ids)))
    src_spans = [s for s in session.scalars(src_stmt).all() if len(s.text) >= MIN_SPAN_CHARS]
    _ensure_embeddings(session, src_spans, "src")

    if not doc_spans or not src_spans:
        run = AnalysisRun(
            detector_id=DETECTOR_ID,
            detector_version=DETECTOR_VERSION,
            inputs={"document_id": str(document_id)},
            outputs_summary={"match_count": 0, "reason": "empty corpus"},
            finished_at=datetime.now(timezone.utc),
        )
        session.add(run)
        session.commit()
        return run.id, 0

    # For each document span, fetch top-k nearest source spans by cosine.
    # We pass a SourceSpan id allow-list when source_ids provided.
    src_id_filter_sql = ""
    params: dict = {}
    if source_ids is not None:
        src_id_filter_sql = "AND ss.source_id = ANY(:source_ids)"
        params["source_ids"] = list(source_ids)

    sql = text(
        f"""
        SELECT ss.id, 1 - (ss.embedding <=> CAST(:vec AS vector)) AS sim
        FROM source_span ss
        WHERE ss.embedding IS NOT NULL
        {src_id_filter_sql}
        ORDER BY ss.embedding <=> CAST(:vec AS vector)
        LIMIT :k
        """
    )

    matches: dict[uuid.UUID, list[tuple[uuid.UUID, float]]] = defaultdict(list)
    src_text_by_id = {s.id: s.text for s in src_spans}

    for d in doc_spans:
        if d.embedding is None:
            continue
        rows = session.execute(
            sql, {**params, "vec": list(d.embedding), "k": TOP_K}
        ).all()
        for row in rows:
            sim = float(row.sim)
            if sim < SIM_THRESHOLD:
                continue
            src_id = row.id
            if src_id not in src_text_by_id:
                continue
            # Suppress matches the n-gram detector would have caught.
            ngram_overlap = jaccard(fingerprint(d.text), fingerprint(src_text_by_id[src_id]))
            if ngram_overlap > NGRAM_OVERLAP_MAX:
                continue
            matches[d.id].append((src_id, sim))

    run = AnalysisRun(
        detector_id=DETECTOR_ID,
        detector_version=DETECTOR_VERSION,
        model="paraphrase-multilingual-MiniLM-L12-v2",
        inputs={
            "document_id": str(document_id),
            "source_ids": [str(s) for s in source_ids] if source_ids else "all",
            "params": {
                "sim_threshold": SIM_THRESHOLD,
                "ngram_overlap_max": NGRAM_OVERLAP_MAX,
                "top_k": TOP_K,
                "min_span_chars": MIN_SPAN_CHARS,
            },
        },
        outputs_summary={"match_count": sum(len(v) for v in matches.values())},
        finished_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    findings_created = 0
    for d_id, ms in matches.items():
        ms.sort(key=lambda t: t[1], reverse=True)
        top_score = ms[0][1]
        finding = Finding(
            document_span_id=d_id,
            source_span_ids=[s_id for s_id, _ in ms],
            kind="paraphrase",
            detector_id=DETECTOR_ID,
            detector_version=DETECTOR_VERSION,
            confidence_category="requires_review",
            status="unreviewed",
            similarity_score=top_score,
            analysis_run_id=run.id,
        )
        session.add(finding)
        findings_created += 1

    session.commit()
    return run.id, findings_created
