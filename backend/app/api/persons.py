from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record as audit_record
from app.db import get_session
from app.models import Document, DocumentSpan, Finding, Person
from app.schemas import (
    DocumentOut,
    PersonDetail,
    PersonIn,
    PersonOut,
    PersonUpdate,
)

router = APIRouter(prefix="/persons", tags=["persons"])


@router.post("", response_model=PersonOut, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonIn, session: Session = Depends(get_session)) -> PersonOut:
    person = Person(
        id=uuid.uuid4(),
        display_name=payload.display_name,
        roles=payload.roles,
        legal_sensitivity_flag=payload.legal_sensitivity_flag,
        right_of_reply_url=payload.right_of_reply_url,
    )
    session.add(person)
    session.flush()
    audit_record(
        session,
        actor="user:editorial",
        action="person.created",
        entity_type="person",
        entity_id=person.id,
        payload={"display_name": person.display_name, "roles": person.roles},
    )
    session.commit()
    session.refresh(person)
    return PersonOut.model_validate(person)


@router.get("", response_model=list[PersonOut])
def list_persons(session: Session = Depends(get_session)) -> list[PersonOut]:
    persons = session.scalars(select(Person).order_by(Person.display_name)).all()
    return [PersonOut.model_validate(p) for p in persons]


@router.get("/{person_id}", response_model=PersonDetail)
def get_person(
    person_id: uuid.UUID, session: Session = Depends(get_session)
) -> PersonDetail:
    person = session.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    documents = session.scalars(
        select(Document).where(Document.person_id == person_id).order_by(Document.year.desc())
    ).all()

    doc_ids = [d.id for d in documents]
    if doc_ids:
        documented = session.scalar(
            select(func.count(Finding.id))
            .join(DocumentSpan, DocumentSpan.id == Finding.document_span_id)
            .where(DocumentSpan.document_id.in_(doc_ids))
            .where(Finding.status == "confirmed")
        ) or 0
        under_review = session.scalar(
            select(func.count(Finding.id))
            .join(DocumentSpan, DocumentSpan.id == Finding.document_span_id)
            .where(DocumentSpan.document_id.in_(doc_ids))
            .where(Finding.status == "unreviewed")
        ) or 0
    else:
        documented = 0
        under_review = 0

    return PersonDetail(
        person=PersonOut.model_validate(person),
        documents=[DocumentOut.model_validate(d) for d in documents],
        documented_findings=documented,
        findings_under_review=under_review,
    )


@router.patch("/{person_id}", response_model=PersonOut)
def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    session: Session = Depends(get_session),
) -> PersonOut:
    person = session.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    data = payload.model_dump(exclude_unset=True)
    before = {k: getattr(person, k) for k in data.keys()}
    for k, v in data.items():
        setattr(person, k, v)
    audit_record(
        session,
        actor="user:editorial",
        action="person.updated",
        entity_type="person",
        entity_id=person.id,
        payload={"before": before, "after": data},
    )
    session.commit()
    session.refresh(person)
    return PersonOut.model_validate(person)


@router.post("/{person_id}/documents/{document_id}", response_model=DocumentOut)
def link_document(
    person_id: uuid.UUID,
    document_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> DocumentOut:
    person = session.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    document.person_id = person.id
    audit_record(
        session,
        actor="user:editorial",
        action="document.linked_to_person",
        entity_type="document",
        entity_id=document.id,
        payload={"person_id": str(person.id)},
    )
    session.commit()
    session.refresh(document)
    return DocumentOut.model_validate(document)
