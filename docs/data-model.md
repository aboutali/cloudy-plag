# Data Model

Relational by default. Default store: **Postgres + pgvector + S3-compatible object storage for PDFs**. Defer Neo4j until citation-graph queries demand it.

## Core Entities

### `Person`
A public figure whose dissertation is in scope.
- `id`
- `display_name`
- `roles` — public roles that justify scrutiny (elected office, senior public administration, public claims of expertise based on the doctorate)
- `legal_sensitivity_flag` — boolean; raises review threshold
- `right_of_reply_url` — link to person's published response, if any

### `Document`
A dissertation (or analogous work).
- `id`
- `person_id` → `Person`
- `title`, `year`, `institution`, `degree`
- `pdf_object_key` — pointer to immutable object storage
- `canonical_hash` — SHA-256 of original PDF
- `provenance` — `{source_url, fetched_at, license}`

### `DocumentSpan`
The addressable unit. Every finding ultimately points here.
- `id`
- `document_id` → `Document`
- `page`
- `bbox` — `(x0, y0, x1, y1)` on the page
- `text` — extracted text content
- `section_path` — e.g. `["3", "3.2", "3.2.1"]`

### `Source`
An external work compared against (book, paper, webpage, prior dissertation).
- `id`
- `kind` — `book | paper | webpage | dissertation | other`
- `citation_metadata` — title, authors, year, identifiers (DOI, ISBN, URL)
- `archived_copy_key` — optional pointer to a stored snapshot (object storage)

### `SourceSpan`
Analogous to `DocumentSpan` but on the source side.
- `id`
- `source_id` → `Source`
- `locator` — page/section/URL anchor as appropriate
- `text`

### `Finding`
The atomic unit of scrutiny. Links one `DocumentSpan` to zero or more `SourceSpan`s.
- `id`
- `document_span_id` → `DocumentSpan`
- `source_span_ids` → `SourceSpan[]` (empty for pure rigor/originality findings)
- `kind` — `text_reuse | translation | paraphrase | ai_generated_suspicion | unsupported_claim | weak_method | originality_doubt`
- `detector_id`, `detector_version`
- `confidence_category` — `requires_review | documented` (no percentages, see `evidence-model.md`)
- `status` — `unreviewed | confirmed | rejected | disputed`
- `analysis_run_id` → `AnalysisRun`
- `created_at`

### `Review`
A reviewer's decision on a finding.
- `id`
- `finding_id` → `Finding`
- `reviewer_id`
- `decision` — `confirm | reject | dispute | request_more_evidence`
- `rationale`
- `created_at`

### `AnalysisRun`
For full reproducibility of any displayed claim.
- `id`
- `model` — e.g. `claude-opus-4-7`, `gte-large`
- `version`
- `prompt_hash` — SHA-256 of the exact prompt template + inputs
- `inputs` — structured pointer to document/source spans consumed
- `outputs` — raw structured output before reviewer triage
- `started_at`, `finished_at`

### `Reviewer`
- `id`
- `handle` — pseudonymous display name acceptable
- `verified_identity` — boolean; required for issuing `confirmed` status on legally-sensitive findings
- `roles` — `triager | reviewer | editor_in_chief`

## Relationships at a glance

```
Person 1—n Document 1—n DocumentSpan
                              \
                               n
Source 1—n SourceSpan        Finding —n— Review
                               |
                               1
                          AnalysisRun
```

## Storage choices

- **Vectors:** `pgvector` columns on `DocumentSpan` and `SourceSpan` for semantic match.
- **PDFs and source snapshots:** S3-compatible object storage; never inline in Postgres.
- **Audit log:** append-only table per write-event (see `architecture.md` §7); never edited.
- **Citation graph:** materialize as Postgres tables with recursive CTEs for now. Re-evaluate Neo4j once citation-graph queries dominate workload.

## Non-negotiables

- A `Finding` is never deleted. It is `rejected` or `disputed`. Corrections are visible, not silent (see `legal-guardrails.md`).
- Every `Finding` displayed publicly has at least one inspectable artifact reachable from the data (see `evidence-model.md`).
- Every public claim must trace through `Finding → AnalysisRun` to a reproducible model invocation.
