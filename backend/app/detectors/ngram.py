"""Character n-gram fingerprinting for text-reuse detection.

Uses a winnowing-style approach (Schleimer et al., SIGMOD 2003) on
character k-grams to produce a robust, position-stable fingerprint.
Spans are compared by Jaccard similarity over their fingerprint sets.

This is a *lead generator*. A finding it produces is `requires_review` and
must be confirmed by a human reviewer before publication. See
docs/evidence-model.md.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AnalysisRun,
    Document,
    DocumentSpan,
    Finding,
    Source,
    SourceSpan,
)

DETECTOR_ID = "ngram_winnow"
DETECTOR_VERSION = "0.1.0"

K = 25  # k-gram size in characters
W = 10  # winnowing window size
MIN_SCORE = 0.18  # Jaccard threshold for a lead
MIN_SPAN_CHARS = 80  # ignore very short spans (boilerplate, headings)


_NORMALIZE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _NORMALIZE.sub(" ", text.lower()).strip()


def _kgrams(text: str, k: int = K) -> list[str]:
    if len(text) < k:
        return []
    return [text[i : i + k] for i in range(len(text) - k + 1)]


def _hash(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")


def fingerprint(text: str, k: int = K, w: int = W) -> set[int]:
    """Winnowing fingerprint: keep min hash within each sliding window of w hashes."""
    norm = _normalize(text)
    grams = _kgrams(norm, k)
    if not grams:
        return set()
    hashes = [_hash(g) for g in grams]
    if len(hashes) < w:
        return {min(hashes)}
    out: set[int] = set()
    last_min_idx = -1
    for i in range(len(hashes) - w + 1):
        window = hashes[i : i + w]
        # rightmost minimum (winnowing rule)
        min_val = min(window)
        min_idx = i + max(j for j, h in enumerate(window) if h == min_val)
        if min_idx != last_min_idx:
            out.add(min_val)
            last_min_idx = min_idx
    return out


def jaccard(a: set[int], b: set[int]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


@dataclass
class Match:
    document_span_id: uuid.UUID
    source_span_id: uuid.UUID
    score: float


def _stopword_filter(fp: set[int], doc_freq: dict[int, int], min_df: int) -> set[int]:
    """Remove fingerprints that appear in too many source spans (boilerplate)."""
    return {h for h in fp if doc_freq.get(h, 0) <= min_df}


def find_matches(
    doc_span_fps: dict[uuid.UUID, set[int]],
    source_span_fps: dict[uuid.UUID, set[int]],
    min_score: float = MIN_SCORE,
) -> list[Match]:
    # Common-knowledge filter: drop fingerprints that appear in many source spans.
    df: dict[int, int] = defaultdict(int)
    for fp in source_span_fps.values():
        for h in fp:
            df[h] += 1
    boilerplate_threshold = max(3, len(source_span_fps) // 10)

    inverted: dict[int, list[uuid.UUID]] = defaultdict(list)
    for span_id, fp in source_span_fps.items():
        filtered = _stopword_filter(fp, df, boilerplate_threshold)
        for h in filtered:
            inverted[h].append(span_id)

    matches: list[Match] = []
    for d_id, d_fp in doc_span_fps.items():
        d_filtered = _stopword_filter(d_fp, df, boilerplate_threshold)
        if not d_filtered:
            continue
        candidate_counts: dict[uuid.UUID, int] = defaultdict(int)
        for h in d_filtered:
            for s_id in inverted.get(h, ()):
                candidate_counts[s_id] += 1
        for s_id, _ in candidate_counts.items():
            score = jaccard(d_filtered, _stopword_filter(source_span_fps[s_id], df, boilerplate_threshold))
            if score >= min_score:
                matches.append(Match(d_id, s_id, score))
    return matches


def run_detector(
    session: Session,
    document_id: uuid.UUID,
    source_ids: Iterable[uuid.UUID] | None = None,
) -> tuple[uuid.UUID, int]:
    """Run the n-gram detector on one document against the given sources (or all)."""
    document = session.get(Document, document_id)
    if document is None:
        raise ValueError(f"Document {document_id} not found")

    doc_spans = session.scalars(
        select(DocumentSpan).where(DocumentSpan.document_id == document_id)
    ).all()
    doc_spans = [s for s in doc_spans if len(s.text) >= MIN_SPAN_CHARS]

    if source_ids is None:
        source_span_rows = session.scalars(select(SourceSpan)).all()
    else:
        source_span_rows = session.scalars(
            select(SourceSpan).where(SourceSpan.source_id.in_(list(source_ids)))
        ).all()
    source_span_rows = [s for s in source_span_rows if len(s.text) >= MIN_SPAN_CHARS]

    doc_fps = {s.id: fingerprint(s.text) for s in doc_spans}
    src_fps = {s.id: fingerprint(s.text) for s in source_span_rows}

    matches = find_matches(doc_fps, src_fps)

    run = AnalysisRun(
        id=uuid.uuid4(),
        detector_id=DETECTOR_ID,
        detector_version=DETECTOR_VERSION,
        inputs={
            "document_id": str(document_id),
            "source_ids": [str(s) for s in source_ids] if source_ids else "all",
            "params": {"k": K, "w": W, "min_score": MIN_SCORE, "min_span_chars": MIN_SPAN_CHARS},
        },
        outputs_summary={"match_count": len(matches)},
        finished_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    # Group matches by document_span so a single Finding can list multiple SourceSpans.
    by_doc: dict[uuid.UUID, list[Match]] = defaultdict(list)
    for m in matches:
        by_doc[m.document_span_id].append(m)

    findings_created = 0
    for doc_span_id, ms in by_doc.items():
        ms.sort(key=lambda m: m.score, reverse=True)
        top_score = ms[0].score
        finding = Finding(
            id=uuid.uuid4(),
            document_span_id=doc_span_id,
            source_span_ids=[m.source_span_id for m in ms],
            kind="text_reuse",
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
