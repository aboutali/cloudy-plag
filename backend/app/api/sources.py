from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record as audit_record
from app.db import get_session
from app.html_extract import extract_main_text
from app.models import Source, SourceSpan
from app.schemas import (
    SourceIngestResponse,
    SourceIngestText,
    SourceIngestUrl,
    SourceOut,
    SourceSpanOut,
)
from app.segmentation import segment_into_spans

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_source_text(
    payload: SourceIngestText,
    session: Session = Depends(get_session),
) -> SourceIngestResponse:
    canonical_hash = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()

    existing = session.scalar(select(Source).where(Source.canonical_hash == canonical_hash))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source already ingested (id={existing.id}).",
        )

    source = Source(
        id=uuid.uuid4(),
        kind=payload.kind,
        title=payload.title,
        authors=payload.authors,
        year=payload.year,
        identifiers=payload.identifiers,
        canonical_hash=canonical_hash,
    )
    session.add(source)
    session.flush()

    spans = segment_into_spans(payload.text)
    for s in spans:
        session.add(SourceSpan(source_id=source.id, text=s))
    audit_record(
        session,
        actor="user:editorial",
        action="source.ingested",
        entity_type="source",
        entity_id=source.id,
        payload={
            "kind": payload.kind,
            "title": payload.title,
            "span_count": len(spans),
            "via": "text",
        },
    )
    session.commit()
    session.refresh(source)

    return SourceIngestResponse(
        source=SourceOut.model_validate(source),
        span_count=len(spans),
    )


@router.post(
    "/from-url",
    response_model=SourceIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_source_url(
    payload: SourceIngestUrl,
    session: Session = Depends(get_session),
) -> SourceIngestResponse:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": "cloudy-plag/0.0.1"},
    ) as client:
        response = await client.get(payload.url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Source returned HTTP {response.status_code}",
        )
    extracted = extract_main_text(response.text)
    if not extracted.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable content extracted from URL.",
        )

    title = payload.title or extracted.title or payload.url
    canonical_hash = hashlib.sha256(extracted.text.encode("utf-8")).hexdigest()

    existing = session.scalar(select(Source).where(Source.canonical_hash == canonical_hash))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source already ingested (id={existing.id}).",
        )

    identifiers = {"url": payload.url, "fetched_at": datetime.now(timezone.utc).isoformat()}
    source = Source(
        id=uuid.uuid4(),
        kind=payload.kind,
        title=title,
        authors=payload.authors,
        year=payload.year,
        identifiers=identifiers,
        canonical_hash=canonical_hash,
    )
    session.add(source)
    session.flush()
    spans = segment_into_spans(extracted.text)
    for s in spans:
        session.add(SourceSpan(source_id=source.id, text=s))
    audit_record(
        session,
        actor="user:editorial",
        action="source.ingested",
        entity_type="source",
        entity_id=source.id,
        payload={
            "kind": payload.kind,
            "title": title,
            "span_count": len(spans),
            "via": "url",
            "url": payload.url,
        },
    )
    session.commit()
    session.refresh(source)
    return SourceIngestResponse(
        source=SourceOut.model_validate(source),
        span_count=len(spans),
    )


@router.get("", response_model=list[SourceOut])
def list_sources(session: Session = Depends(get_session)) -> list[SourceOut]:
    sources = session.scalars(select(Source).order_by(Source.created_at.desc())).all()
    return [SourceOut.model_validate(s) for s in sources]


@router.get("/{source_id}/spans", response_model=list[SourceSpanOut])
def list_source_spans(
    source_id: uuid.UUID, session: Session = Depends(get_session)
) -> list[SourceSpanOut]:
    if session.get(Source, source_id) is None:
        raise HTTPException(status_code=404, detail="Source not found")
    spans = session.scalars(
        select(SourceSpan).where(SourceSpan.source_id == source_id)
    ).all()
    return [SourceSpanOut.model_validate(s) for s in spans]
