"""Helper for recording audit events.

Use within a request-handling session. Caller commits as part of their
normal transaction so the event lives or dies with the change it describes.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {},
    )
    session.add(event)
    return event
