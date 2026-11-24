from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonIn(BaseModel):
    display_name: str
    roles: list[str] | None = None
    legal_sensitivity_flag: bool = False
    right_of_reply_url: str | None = None


class PersonUpdate(BaseModel):
    display_name: str | None = None
    roles: list[str] | None = None
    legal_sensitivity_flag: bool | None = None
    right_of_reply_url: str | None = None


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    roles: list[str] | None = None
    legal_sensitivity_flag: bool
    right_of_reply_url: str | None = None
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID | None = None
    title: str
    year: int | None = None
    institution: str | None = None
    degree: str | None = None
    canonical_hash: str
    provenance: dict
    created_at: datetime


class PersonDetail(BaseModel):
    person: PersonOut
    documents: list[DocumentOut]
    documented_findings: int
    findings_under_review: int


class DocumentIngestResponse(BaseModel):
    document: DocumentOut
    span_count: int


class DocumentSpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    page: int
    bbox_x0: float
    bbox_y0: float
    bbox_x1: float
    bbox_y1: float
    text: str


class IngestUrlRequest(BaseModel):
    url: str = Field(..., description="HTTPS URL to a PDF (e.g. DNB landing page resolver)")
    title: str
    year: int | None = None
    institution: str | None = None
    degree: str | None = None
    person_id: uuid.UUID | None = None


class SourceIngestText(BaseModel):
    kind: str = Field(..., description="book|paper|webpage|dissertation|other")
    title: str
    authors: list[str] | None = None
    year: int | None = None
    identifiers: dict = Field(default_factory=dict)
    text: str


class SourceIngestUrl(BaseModel):
    url: str
    kind: str = "webpage"
    title: str | None = None
    authors: list[str] | None = None
    year: int | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    authors: list[str] | None = None
    year: int | None = None
    identifiers: dict
    canonical_hash: str
    created_at: datetime


class SourceIngestResponse(BaseModel):
    source: SourceOut
    span_count: int


class SourceSpanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    locator: str | None = None
    text: str


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_span_id: uuid.UUID
    source_span_ids: list[uuid.UUID]
    kind: str
    detector_id: str
    detector_version: str
    confidence_category: str
    status: str
    rationale: str | None = None
    created_at: datetime


class FindingDetail(BaseModel):
    finding: FindingOut
    document_span: DocumentSpanOut
    source_spans: list[SourceSpanOut]


class ReviewIn(BaseModel):
    reviewer_handle: str
    decision: str = Field(..., description="confirm|reject|dispute|request_more_evidence")
    rationale: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    rationale: str | None = None
    created_at: datetime


class DetectorRunRequest(BaseModel):
    document_id: uuid.UUID
    source_ids: list[uuid.UUID] | None = None  # None = all sources


class DetectorRunResponse(BaseModel):
    analysis_run_id: uuid.UUID
    findings_created: int
