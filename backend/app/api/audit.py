from __future__ import annotations

import json
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


def _serialize(e: AuditEvent) -> dict:
    return {
        "id": str(e.id),
        "occurred_at": e.occurred_at.isoformat(),
        "actor": e.actor,
        "action": e.action,
        "entity_type": e.entity_type,
        "entity_id": str(e.entity_id) if e.entity_id else None,
        "payload": e.payload,
    }


@router.get("/events.jsonl")
def export_events(
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    session: Session = Depends(get_session),
) -> StreamingResponse:
    stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc())
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    stmt = stmt.limit(limit)
    events = session.scalars(stmt).all()

    def gen() -> Iterator[bytes]:
        for e in events:
            yield (json.dumps(_serialize(e), ensure_ascii=False) + "\n").encode("utf-8")

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@router.get("/events", response_model=list[dict])
def list_events(
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
) -> list[dict]:
    stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc())
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    stmt = stmt.limit(limit)
    return [_serialize(e) for e in session.scalars(stmt).all()]
