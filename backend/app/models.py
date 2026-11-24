from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# Controlled vocabulary — see docs/legal-guardrails.md
FINDING_KINDS = (
    "text_reuse",
    "translation",
    "paraphrase",
    "ai_generated_suspicion",
    "unsupported_claim",
    "weak_method",
    "originality_doubt",
)
FINDING_STATUSES = ("unreviewed", "confirmed", "rejected", "disputed")
CONFIDENCE_CATEGORIES = ("requires_review", "documented")
REVIEW_DECISIONS = ("confirm", "reject", "dispute", "request_more_evidence")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Person(Base):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    roles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    legal_sensitivity_flag: Mapped[bool] = mapped_column(default=False, nullable=False)
    right_of_reply_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    documents: Mapped[list[Document]] = relationship(back_populates="person")


class Document(Base):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    year: Mapped[int | None] = mapped_column(nullable=True)
    institution: Mapped[str | None] = mapped_column(String(256), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pdf_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    person: Mapped[Person | None] = relationship(back_populates="documents")
    spans: Mapped[list[DocumentSpan]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentSpan(Base):
    __tablename__ = "document_span"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id"), nullable=False
    )
    page: Mapped[int] = mapped_column(nullable=False)
    bbox_x0: Mapped[float] = mapped_column(nullable=False)
    bbox_y0: Mapped[float] = mapped_column(nullable=False)
    bbox_x1: Mapped[float] = mapped_column(nullable=False)
    bbox_y1: Mapped[float] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section_path: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    document: Mapped[Document] = relationship(back_populates="spans")

    __table_args__ = (Index("ix_document_span_doc_page", "document_id", "page"),)


class Source(Base):
    __tablename__ = "source"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # book|paper|webpage|dissertation|other
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    authors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    year: Mapped[int | None] = mapped_column(nullable=True)
    identifiers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # doi, isbn, url
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    archived_copy_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    spans: Mapped[list[SourceSpan]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceSpan(Base):
    __tablename__ = "source_span"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source.id", ondelete="CASCADE"), nullable=False
    )
    locator: Mapped[str | None] = mapped_column(String(256), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    source: Mapped[Source] = relationship(back_populates="spans")

    __table_args__ = (Index("ix_source_span_source", "source_id"),)


class AnalysisRun(Base):
    __tablename__ = "analysis_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    detector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    outputs_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)


class Reviewer(Base):
    __tablename__ = "reviewer"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    handle: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    verified_identity: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="reviewer")  # triager|reviewer|editor_in_chief
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class Finding(Base):
    __tablename__ = "finding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    document_span_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_span.id", ondelete="CASCADE"), nullable=False
    )
    source_span_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    detector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="requires_review"
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unreviewed")
    similarity_score: Mapped[float | None] = mapped_column(nullable=True)  # internal only
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_run.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    document_span: Mapped[DocumentSpan] = relationship()
    reviews: Mapped[list[Review]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_finding_document_span", "document_span_id"),
        Index("ix_finding_status", "status"),
    )


class Review(Base):
    __tablename__ = "review"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewer.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    finding: Mapped[Finding] = relationship(back_populates="reviews")


class AuditEvent(Base):
    """Append-only event log. See docs/architecture.md §7.

    Insert-only by application convention; a database trigger blocks UPDATE
    and DELETE on this table.
    """

    __tablename__ = "audit_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_audit_event_entity", "entity_type", "entity_id"),
        Index("ix_audit_event_occurred_at", "occurred_at"),
    )
