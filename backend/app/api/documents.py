from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record as audit_record
from app.db import get_session
from app.extraction import extract_spans
from app import grobid
from app.models import Document, DocumentSpan
from app.schemas import (
    DocumentIngestResponse,
    DocumentOut,
    DocumentSpanOut,
    IngestUrlRequest,
)
from app.storage import get_object_bytes, object_exists, put_object
from fastapi.responses import Response

router = APIRouter(prefix="/documents", tags=["documents"])


def _hash_and_key(pdf_bytes: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    return digest, f"documents/{digest}.pdf"


def _ingest_pdf(
    session: Session,
    pdf_bytes: bytes,
    title: str,
    year: int | None,
    institution: str | None,
    degree: str | None,
    source_url: str | None,
    person_id: uuid.UUID | None = None,
    use_grobid: bool = False,
) -> DocumentIngestResponse:
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded data is not a PDF (missing %PDF header).",
        )

    canonical_hash, object_key = _hash_and_key(pdf_bytes)

    existing = session.scalar(
        select(Document).where(Document.canonical_hash == canonical_hash)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document already ingested (id={existing.id}).",
        )

    if not object_exists(object_key):
        put_object(object_key, pdf_bytes)

    provenance = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "license": None,
    }

    document = Document(
        id=uuid.uuid4(),
        person_id=person_id,
        title=title,
        year=year,
        institution=institution,
        degree=degree,
        pdf_object_key=object_key,
        canonical_hash=canonical_hash,
        provenance=provenance,
    )
    session.add(document)
    session.flush()

    extractor_used = "pdfplumber"
    grobid_spans: list = []
    if use_grobid and grobid.is_available():
        try:
            grobid_spans = grobid.extract_via_grobid(pdf_bytes)
            extractor_used = "grobid" if grobid_spans else "pdfplumber"
        except Exception:
            grobid_spans = []
            extractor_used = "pdfplumber"

    if grobid_spans:
        for s in grobid_spans:
            session.add(
                DocumentSpan(
                    document_id=document.id,
                    page=s.page,
                    bbox_x0=s.bbox[0],
                    bbox_y0=s.bbox[1],
                    bbox_x1=s.bbox[2],
                    bbox_y1=s.bbox[3],
                    text=s.text,
                    section_path=s.section_path or None,
                )
            )
        extracted = grobid_spans
    else:
        extracted = extract_spans(pdf_bytes)
        for s in extracted:
            session.add(
                DocumentSpan(
                    document_id=document.id,
                    page=s.page,
                    bbox_x0=s.bbox[0],
                    bbox_y0=s.bbox[1],
                    bbox_x1=s.bbox[2],
                    bbox_y1=s.bbox[3],
                    text=s.text,
                )
            )
    audit_record(
        session,
        actor="system:ingest",
        action="document.ingested",
        entity_type="document",
        entity_id=document.id,
        payload={
            "title": title,
            "canonical_hash": canonical_hash,
            "span_count": len(extracted),
            "source_url": source_url,
            "person_id": str(person_id) if person_id else None,
            "extractor": extractor_used,
        },
    )
    session.commit()
    session.refresh(document)

    return DocumentIngestResponse(
        document=DocumentOut.model_validate(document),
        span_count=len(extracted),
    )


@router.post("", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    year: int | None = Form(None),
    institution: str | None = Form(None),
    degree: str | None = Form(None),
    person_id: uuid.UUID | None = Form(None),
    use_grobid: bool = Form(False),
    session: Session = Depends(get_session),
) -> DocumentIngestResponse:
    pdf_bytes = await file.read()
    return _ingest_pdf(
        session,
        pdf_bytes,
        title=title,
        year=year,
        institution=institution,
        degree=degree,
        source_url=None,
        person_id=person_id,
        use_grobid=use_grobid,
    )


@router.post("/from-url", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document_from_url(
    payload: IngestUrlRequest,
    session: Session = Depends(get_session),
) -> DocumentIngestResponse:
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(payload.url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Source returned HTTP {response.status_code}",
        )
    return _ingest_pdf(
        session,
        response.content,
        title=payload.title,
        year=payload.year,
        institution=payload.institution,
        degree=payload.degree,
        source_url=payload.url,
        person_id=payload.person_id,
    )


@router.get("", response_model=list[DocumentOut])
def list_documents(session: Session = Depends(get_session)) -> list[DocumentOut]:
    docs = session.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, session: Session = Depends(get_session)) -> DocumentOut:
    doc = session.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}/pdf")
def get_document_pdf(document_id: uuid.UUID, session: Session = Depends(get_session)) -> Response:
    doc = session.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    pdf_bytes = get_object_bytes(doc.pdf_object_key)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/{document_id}/spans", response_model=list[DocumentSpanOut])
def list_document_spans(
    document_id: uuid.UUID,
    page: int | None = None,
    session: Session = Depends(get_session),
) -> list[DocumentSpanOut]:
    if session.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    stmt = select(DocumentSpan).where(DocumentSpan.document_id == document_id)
    if page is not None:
        stmt = stmt.where(DocumentSpan.page == page)
    stmt = stmt.order_by(DocumentSpan.page, DocumentSpan.bbox_y0, DocumentSpan.bbox_x0)
    spans = session.scalars(stmt).all()
    return [DocumentSpanOut.model_validate(s) for s in spans]
