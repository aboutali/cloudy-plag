from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record as audit_record
from app.db import get_session
from app.detectors import ngram, paraphrase
from app.models import (
    REVIEW_DECISIONS,
    Document,
    DocumentSpan,
    Finding,
    Review,
    Reviewer,
    SourceSpan,
)
from app.schemas import (
    DetectorRunRequest,
    DetectorRunResponse,
    DocumentSpanOut,
    FindingDetail,
    FindingOut,
    ReviewIn,
    ReviewOut,
    SourceSpanOut,
)

router = APIRouter(tags=["findings"])


# Findings requiring two confirms before becoming `documented` (see evidence-model.md).
TWO_CONFIRMS_REQUIRED = {"paraphrase", "unsupported_claim", "originality_doubt"}
# Findings that require editor-in-chief sign-off and stay reviewer-only by default.
EDITOR_GATED = {"weak_method"}
# Findings never published as standalone evidence.
NEVER_STANDALONE = {"ai_generated_suspicion"}


def _confirm_count(finding: Finding) -> int:
    return sum(1 for r in finding.reviews if r.decision == "confirm")


def _editor_confirm_count(finding: Finding, session: Session) -> int:
    count = 0
    for r in finding.reviews:
        if r.decision != "confirm":
            continue
        reviewer = session.get(Reviewer, r.reviewer_id)
        if reviewer and reviewer.role == "editor_in_chief":
            count += 1
    return count


def _recompute_status(finding: Finding, session: Session) -> None:
    """Apply evidence-model rules to recompute Finding.status & confidence."""
    decisions = [r.decision for r in finding.reviews]
    if "dispute" in decisions:
        finding.status = "disputed"
        finding.confidence_category = "requires_review"
        return
    if "reject" in decisions:
        finding.status = "rejected"
        finding.confidence_category = "requires_review"
        return

    if finding.kind in NEVER_STANDALONE:
        finding.status = "unreviewed"
        finding.confidence_category = "requires_review"
        return

    confirms = _confirm_count(finding)
    if finding.kind in EDITOR_GATED:
        if _editor_confirm_count(finding, session) >= 1:
            finding.status = "confirmed"
            finding.confidence_category = "documented"
        return

    required = 2 if finding.kind in TWO_CONFIRMS_REQUIRED else 1
    if confirms >= required:
        finding.status = "confirmed"
        finding.confidence_category = "documented"


@router.get("/documents/{document_id}/findings", response_model=list[FindingOut])
def list_document_findings(
    document_id: uuid.UUID,
    status_filter: str | None = None,
    session: Session = Depends(get_session),
) -> list[FindingOut]:
    if session.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    stmt = (
        select(Finding)
        .join(DocumentSpan, DocumentSpan.id == Finding.document_span_id)
        .where(DocumentSpan.document_id == document_id)
        .order_by(Finding.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(Finding.status == status_filter)
    findings = session.scalars(stmt).all()
    return [FindingOut.model_validate(f) for f in findings]


@router.get("/findings/{finding_id}", response_model=FindingDetail)
def get_finding(
    finding_id: uuid.UUID, session: Session = Depends(get_session)
) -> FindingDetail:
    finding = session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    doc_span = session.get(DocumentSpan, finding.document_span_id)
    source_spans = session.scalars(
        select(SourceSpan).where(SourceSpan.id.in_(finding.source_span_ids))
    ).all()
    return FindingDetail(
        finding=FindingOut.model_validate(finding),
        document_span=DocumentSpanOut.model_validate(doc_span),
        source_spans=[SourceSpanOut.model_validate(s) for s in source_spans],
    )


@router.post(
    "/findings/{finding_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_review(
    finding_id: uuid.UUID,
    payload: ReviewIn,
    session: Session = Depends(get_session),
) -> ReviewOut:
    if payload.decision not in REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail=f"Invalid decision: {payload.decision}")

    finding = session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    reviewer = session.scalar(
        select(Reviewer).where(Reviewer.handle == payload.reviewer_handle)
    )
    if reviewer is None:
        reviewer = Reviewer(handle=payload.reviewer_handle)
        session.add(reviewer)
        session.flush()

    review = Review(
        finding_id=finding.id,
        reviewer_id=reviewer.id,
        decision=payload.decision,
        rationale=payload.rationale,
    )
    session.add(review)
    session.flush()

    # Refresh the relationship so _recompute_status sees the new review.
    session.refresh(finding)
    prior_status = finding.status
    _recompute_status(finding, session)
    audit_record(
        session,
        actor=f"reviewer:{reviewer.handle}",
        action="finding.reviewed",
        entity_type="finding",
        entity_id=finding.id,
        payload={
            "decision": payload.decision,
            "rationale": payload.rationale,
            "prior_status": prior_status,
            "new_status": finding.status,
            "kind": finding.kind,
        },
    )
    session.commit()
    session.refresh(review)

    return ReviewOut.model_validate(review)


@router.post("/detectors/ngram/run", response_model=DetectorRunResponse)
def run_ngram_detector(
    payload: DetectorRunRequest,
    session: Session = Depends(get_session),
) -> DetectorRunResponse:
    try:
        run_id, count = ngram.run_detector(session, payload.document_id, payload.source_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    audit_record(
        session,
        actor="user:editorial",
        action="detector.ngram.run",
        entity_type="document",
        entity_id=payload.document_id,
        payload={"analysis_run_id": str(run_id), "findings_created": count},
    )
    session.commit()
    return DetectorRunResponse(analysis_run_id=run_id, findings_created=count)


@router.post("/detectors/paraphrase/run", response_model=DetectorRunResponse)
def run_paraphrase_detector(
    payload: DetectorRunRequest,
    session: Session = Depends(get_session),
) -> DetectorRunResponse:
    try:
        run_id, count = paraphrase.run_detector(
            session, payload.document_id, payload.source_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    audit_record(
        session,
        actor="user:editorial",
        action="detector.paraphrase.run",
        entity_type="document",
        entity_id=payload.document_id,
        payload={"analysis_run_id": str(run_id), "findings_created": count},
    )
    session.commit()
    return DetectorRunResponse(analysis_run_id=run_id, findings_created=count)
