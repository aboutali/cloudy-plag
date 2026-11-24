"""Generate a synthetic dissertation PDF + matching source and run the detector.

Usage (inside the backend container):
    python -m app.demo_seed

The script is idempotent against canonical_hash duplicates: if the demo
person/document/source already exist, it skips them and only re-runs the detector.
"""
from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.api.documents import _ingest_pdf
from app.db import SessionLocal
from app.detectors import ngram
from app.models import Person, Source
from app.schemas import SourceIngestText
from app.api.sources import ingest_source_text  # type: ignore

DEMO_PERSON_NAME = "Dr. Demo Beispielmann"
DEMO_DOC_TITLE = "Föderalismus und Handlungsfähigkeit — eine demonstrative Untersuchung"
DEMO_SOURCE_TITLE = "Aufsatz: Föderalismusreform und Handlungsfähigkeit (Demo-Korpus)"


# Two passages that overlap heavily — the detector should flag them.
SHARED_PASSAGE_1 = (
    "Die zentrale These der vorliegenden Arbeit lautet, dass die "
    "Föderalismusreform die Handlungsfähigkeit des Bundes substanziell "
    "erweitert hat, indem sie Kompetenzkonflikte zwischen Bund und Ländern "
    "reduziert und Entscheidungsverfahren beschleunigt hat. Diese Verschiebung "
    "wird im Folgenden anhand dreier Politikfelder rekonstruiert."
)

SHARED_PASSAGE_2 = (
    "Insgesamt zeigt sich, dass die institutionelle Gewaltenverschränkung "
    "im deutschen Bundesstaat durch die Reformen nicht aufgehoben, wohl aber "
    "in eine kooperationsorientierte Routine überführt wurde, deren empirische "
    "Wirkungen in den nachfolgenden Kapiteln im Einzelnen dargelegt werden."
)

DISS_INTRO = (
    "Einleitung. Der vorliegende Beitrag untersucht das Verhältnis von Bund "
    "und Ländern im Lichte der Föderalismusreform 2006 sowie nachfolgender "
    "Anpassungen. Dabei wird ein qualitativ-vergleichender Ansatz gewählt."
)

DISS_OWN = (
    "Methodisch stützt sich die Untersuchung auf eine Auswahl von zwölf "
    "Interviews mit Mitgliedern von Bundes- und Landesverwaltungen sowie auf "
    "die Auswertung legislativer Dokumente aus dem Zeitraum 2006 bis 2018."
)

SOURCE_OWN_INTRO = (
    "Einleitend sei festgehalten, dass die deutsche Föderalismusforschung "
    "seit langem eine Diskussion über die Effektivität der Kompetenzverteilung "
    "führt."
)

SOURCE_OWN_END = (
    "Diese Diskussion knüpft an klassische Beiträge der vergleichenden "
    "Föderalismusforschung an und bleibt bis heute kontrovers."
)


def build_pdf() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=DEMO_DOC_TITLE)
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.fontName = "Times-Roman"
    body.fontSize = 11
    body.leading = 15
    h1 = styles["Heading1"]

    story = [
        Paragraph(DEMO_DOC_TITLE, h1),
        Spacer(1, 12),
        Paragraph(DISS_INTRO, body),
        Spacer(1, 8),
        Paragraph(SHARED_PASSAGE_1, body),
        Spacer(1, 8),
        Paragraph(DISS_OWN, body),
        Spacer(1, 8),
        Paragraph(SHARED_PASSAGE_2, body),
    ]
    doc.build(story)
    return buffer.getvalue()


def build_source_text() -> str:
    return "\n\n".join([SOURCE_OWN_INTRO, SHARED_PASSAGE_1, SHARED_PASSAGE_2, SOURCE_OWN_END])


def main() -> None:
    pdf_bytes = build_pdf()
    source_text = build_source_text()

    with SessionLocal() as session:
        person = session.query(Person).filter_by(display_name=DEMO_PERSON_NAME).one_or_none()
        if person is None:
            person = Person(
                display_name=DEMO_PERSON_NAME,
                roles=["Demo-Persona", "Politikwissenschaft"],
            )
            session.add(person)
            session.commit()
            session.refresh(person)
            print(f"Created person {person.id}")
        else:
            print(f"Person already exists: {person.id}")

        # Document
        try:
            doc_response = _ingest_pdf(
                session,
                pdf_bytes,
                title=DEMO_DOC_TITLE,
                year=2026,
                institution="Universität Beispielstadt",
                degree="Dr. rer. demo.",
                source_url=None,
                person_id=person.id,
            )
            document_id = doc_response.document.id
            print(f"Created document {document_id} ({doc_response.span_count} spans)")
        except Exception as e:
            print(f"Document ingest skipped: {e}")
            from app.models import Document
            existing = (
                session.query(Document).filter_by(title=DEMO_DOC_TITLE).order_by(Document.created_at.desc()).first()
            )
            if existing is None:
                raise
            document_id = existing.id

        # Source
        existing_source = session.query(Source).filter_by(title=DEMO_SOURCE_TITLE).one_or_none()
        if existing_source is None:
            ingest_source_text(
                SourceIngestText(
                    kind="paper",
                    title=DEMO_SOURCE_TITLE,
                    authors=["Beispielautorin, A."],
                    year=2018,
                    text=source_text,
                ),
                session=session,
            )
            print("Created demo source")
        else:
            print(f"Source already exists: {existing_source.id}")

        # Run detector
        run_id, count = ngram.run_detector(session, document_id)
        print(f"Detector run {run_id}: {count} findings")
        print(f"Open: http://localhost:3001/persons/{person.id}")
        print(f"      http://localhost:3001/documents/{document_id}")


if __name__ == "__main__":
    main()
