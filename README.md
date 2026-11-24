# cloudy-plag

A modern successor to VroniPlag Wiki, reimagined for the GenAI era. Documents — does not accuse — credibility issues in the dissertations of public figures along three axes: **plagiarism**, **originality of ideas**, and **methodological rigor**.

## Quickstart

```bash
cp .env.example .env
make up               # postgres, minio, backend, frontend
make migrate          # run alembic migrations
```

Then:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001 (login from `.env`)

Ingest a PDF:

```bash
curl -F "file=@dissertation.pdf" -F "title=…" -F "year=2010" \
     http://localhost:8000/documents
```

Or from a URL:

```bash
curl -X POST http://localhost:8000/documents/from-url \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.org/diss.pdf", "title": "…"}'
```

Add a candidate source (plain text):

```bash
curl -X POST http://localhost:8000/sources \
     -H "Content-Type: application/json" \
     -d '{"kind":"paper","title":"…","text":"…"}'
```

Run the n-gram detector against a document:

```bash
curl -X POST http://localhost:8000/detectors/ngram/run \
     -H "Content-Type: application/json" \
     -d '{"document_id": "<uuid>"}'
```

Then visit `/review/<uuid>` to triage the leads, or `/documents/<uuid>` to see the side-by-side viewer with bbox overlays.

## Layout

- `backend/` — FastAPI + SQLAlchemy + Alembic. Ingest, extraction, storage.
- `frontend/` — Next.js 15 + TypeScript + Tailwind. Public reading view.
- `docs/` — design brief (see below).

## Design documents

- [`docs/architecture.md`](docs/architecture.md) — components, services, tech stack, hard problems.
- [`docs/data-model.md`](docs/data-model.md) — entities, relationships, storage choices.
- [`docs/evidence-model.md`](docs/evidence-model.md) — the "show your work" contract; what makes a finding publishable.
- [`docs/legal-guardrails.md`](docs/legal-guardrails.md) — German legal framing, controlled vocabulary, takedown SOP, reviewer code of conduct.
- [`docs/roadmap.md`](docs/roadmap.md) — phased plan with explicit go/no-go criteria.

## Core constraints

- **No AI-only publication.** Models generate leads; humans confirm before public display.
- **Show your work.** Every published finding resolves to a citable, human-inspectable artifact (side-by-side comparison, citation-graph snapshot, quoted-claim-with-context).
- **Document, don't accuse.** Controlled vocabulary; no verdict language until an authority has spoken.
- **EU-hosted, German legal context.** §§ 185–187 StGB, Persönlichkeitsrecht, § 51 UrhG, DSGVO.
