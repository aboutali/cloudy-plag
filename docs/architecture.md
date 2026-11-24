# Architecture

A modern successor to VroniPlag Wiki, reimagined for the GenAI era. Scrutinizes dissertations of public figures along three axes: **plagiarism**, **originality of ideas**, **methodological rigor**.

## Guiding Goals

- **Document, don't accuse.** Report verifiable observations; let readers and authorities draw conclusions. Both an epistemic and a legal stance (§§ 185–187 StGB, Persönlichkeitsrecht).
- **Show your work.** Every machine-generated claim must resolve to a citable, side-by-side, human-inspectable artifact. Model verdicts are *leads*, never published evidence.
- **Three scrutiny axes:** plagiarism (textual / translational / paraphrase / AI-generated), originality of ideas, methodological rigor.

## Core Components

Seven loosely-coupled services, each with a clear input/output contract.

### 1. Source Acquisition & Ingest
Crawls DNB, university repositories (BASE, OPUS instances) and accepts manual uploads. Stores canonical PDFs immutably with provenance metadata (URL, fetch date, hash, license).

### 2. Document Processing Pipeline
PDF → structured text (layout-aware, OCR fallback), section/heading segmentation, citation extraction, footnote linking, page/line coordinate preservation. Coordinates matter: every later finding must be addressable as `(doc_id, page, bbox)`.

### 3. Analysis Workers
Three parallel families:
- **Plagiarism** — n-gram fingerprinting against a reference corpus (classical), embedding-based semantic match (paraphrase/translation), AI-text detection (treated as low-confidence signal, never as standalone evidence).
- **Originality** — claim extraction → embedding search against prior literature (OpenAlex, Semantic Scholar, Crossref) → "is this claim novel relative to its citation neighborhood?"
- **Methodological rigor** — LLM-assisted critique structured as rubric items per field (sample size, control, replicability, statistical reporting). Output is always a question-and-citation pair, never a verdict.

### 4. Evidence Store
The crown jewels. Every Fundstelle is a structured record linking source span(s) to target span(s) with an evidence type, a confidence category, and a reviewer status (unreviewed / confirmed / rejected / disputed). See `data-model.md`.

### 5. Review & Curation Layer
Human reviewers triage AI-generated leads. No finding becomes public on a person's page until a reviewer (or quorum) marks it confirmed. AI never publishes directly.

### 6. Public Presentation Layer
Per-document dashboards, side-by-side diff viewers (the VroniPlag visual lineage matters here), aggregate statistics, and clear status badges ("Findings under review" vs. "Documented findings").

### 7. Audit & Versioning
Every finding, every reviewer action, every model run is append-only logged. Reproducibility of any displayed claim is non-negotiable.

## Reviewer / Trust Model

Three viable models. **(b) is recommended.**

- **(a) Open wiki** — maximum throughput, weakest legal posture, vulnerable to coordinated abuse against political targets.
- **(b) Curated editorial with AI triage** *(recommended)* — AI generates leads at scale; a vetted reviewer pool (with named editors-in-chief liable in the impressum sense) confirms before publication. Preserves VroniPlag's careful-craft reputation while exploiting AI scale.
- **(c) Pure automation** — irresponsible given current model reliability and German legal exposure. Reject.

A hybrid is plausible: open lead-submission and commenting, closed publication.

## Tech Stack (proposed default — confirm before committing)

- **Backend:** Python + FastAPI; async workers via Celery or Arq; Redis for queues.
- **Storage:** Postgres + pgvector; S3-compatible object storage (MinIO locally, Hetzner/OVH/Scaleway in EU prod).
- **Frontend:** Next.js + TypeScript. PDF.js with a custom annotation overlay for the side-by-side viewer.
- **Infra:** EU-hosted from day one (GDPR + optics). Containerized; Terraform when scale demands it.

### Genuine alternatives

- **Backend (TS-everywhere):** Next.js + tRPC with a separate Python ML side-service. Reduces context-switching for a small team but pushes ML into a service boundary you'll cross constantly. Take this route only if the team is TS-heavy.
- **Storage (graph DB):** Neo4j becomes attractive once citation-graph originality analysis is the dominant workload. Start in Postgres, migrate the graph subset later if and only if query patterns demand it.

## External Dependencies

- **Corpora:** DNB, BASE, OpenAlex, Crossref, Semantic Scholar, university OPUS instances, Wikipedia/Wikisource for common-knowledge filtering.
- **OCR/Layout:** GROBID for scholarly PDF parsing; Tesseract or a layout model as fallback.
- **LLMs:** Frontier model for claim extraction and rigor critique; smaller open-weights models (self-hosted) for embeddings and high-volume scanning — both for cost and for the option of on-prem when legal review demands it.
- **Identity:** OAuth for reviewers; pseudonymous public reviewer handles acceptable, but real-identity verification for reviewers issuing confirmed findings is worth considering.

## Hard Problems to Watch Early

- **Verifiability of AI-generated rigor critiques** — easiest to be wrong about, most defamation-adjacent. Consider keeping rigor findings reviewer-only far longer than plagiarism findings.
- **Source acquisition at scale** — many dissertations are paywalled or only in print. The reference corpus problem is harder than the detector problem.
- **Adversarial dynamics** — political actors will attempt to discredit, flood, or SLAPP the platform. Threat-model this from day one (rate limiting, reviewer protection, legal counsel on retainer in Germany).
- **Common-knowledge filtering** — distinguishing genuine reuse from boilerplate is the long tail that determines whether the platform feels rigorous or trigger-happy.
