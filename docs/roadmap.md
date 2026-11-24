# Roadmap

Phased build order with explicit go/no-go criteria between phases. Timing is rough; gating criteria are not.

## Phase 0 — Foundations (4–6 weeks)

Goal: a credible legal and infrastructural floor before any analysis runs.

- Ingest pipeline for **one** source (DNB).
- PDF → structured text via GROBID (+ OCR fallback).
- Evidence data model (`docs/data-model.md`) materialized in Postgres.
- Append-only audit log.
- EU hosting + legal entity setup, impressum, DSGVO documentation.
- Takedown SOP published.
- Reviewer code of conduct drafted.

**Go/no-go to Phase 1:**
- Legal counsel has reviewed impressum, takedown SOP, controlled vocabulary.
- Audit log demonstrably append-only (verified by destructive test).
- One end-to-end ingest of a real public dissertation, with all spans addressable as `(doc_id, page, bbox)`.

## Phase 1 — MVP (8–12 weeks)

Goal: prove the evidence-and-review loop works on classical plagiarism alone. No AI claims published yet.

- Classical plagiarism detection only (n-gram fingerprinting against a reference corpus).
- Reviewer dashboard with triage queue.
- Side-by-side viewer (the visual lineage from VroniPlag is the centerpiece UI).
- Pilot on **already-public cases** — historical, settled cases provide a safe baseline to validate the pipeline against known ground truth.
- Right-of-reply mechanism live but not yet exercised.

**Go/no-go to Phase 2:**
- Pipeline reproduces a meaningful subset of an already-public, already-adjudicated case's findings without false positives the reviewers reject.
- Side-by-side viewer renders correctly on representative PDFs (multi-column, footnotes, tables).
- Two named editors-in-chief in place.
- Mean reviewer-to-publication latency measured and acceptable.

## Phase 2 — v1 (3–4 months)

Goal: extend to the detectors classical tools miss. Still leads-only for AI-assisted findings.

- Semantic / paraphrase plagiarism via embedding search.
- Translation plagiarism (cross-lingual semantic match against EN/DE corpora).
- AI-text suspicion detector — **leads only**, never standalone evidence (`evidence-model.md`).
- Public per-person pages with **documented** findings.
- Right-of-reply exercised in production: every person page links any reply.
- First public-figure case published.

**Go/no-go to Phase 3:**
- Zero corrections-required-by-counsel in published findings over the phase.
- Dispute mechanism exercised and resolved at least once on a real finding.
- Reviewer pool ≥ a defined minimum (TBD; suggest 8–12 active reviewers).
- Common-knowledge filter validated against a held-out set of boilerplate passages.

## Phase 3 — Originality & Rigor (4–6 months)

Goal: become a genuine successor, not a VroniPlag clone. This is where the project's GenAI-era thesis is tested.

- Claim extraction over dissertations.
- Citation-graph originality analysis against OpenAlex/Semantic Scholar/Crossref.
- Rubric-based methodological critique (per-field rubrics).
- All outputs **human-gated**; `weak_method` and `originality_doubt` reviewer-only by default.
- Editor-in-chief sign-off required for `weak_method` publication.

**Go/no-go to Phase 4:**
- A documented `originality_doubt` finding survives external scrutiny (e.g., independent academic review or right-of-reply round) without retraction.
- Rubric per major target field (law, political science, medicine, engineering) defined and reviewer-trained.
- No defamation claim filed and unresolved.

## Phase 4 — Scale & Community

Goal: open the funnel without losing the careful-craft reputation.

- Public lead submission (open lead-submission and commenting; closed publication remains the rule).
- Reviewer onboarding program with mentorship.
- Researcher API for the audit log and finding metadata.
- Bulk corpus expansion (more universities, more sources).
- Threat-model refresh under heavier adversarial load.

## Cross-Cutting, Always-On

- Legal counsel on retainer from Phase 0.
- Audit log and reproducibility never regress.
- Controlled-vocabulary enforcement is a CI check on display strings, not a guideline.
- AI-only publication remains a hard prohibition through every phase.
- Confidence is shown as a category, never a percentage.

## Explicit Non-Goals

- No leaderboard or person-level "score".
- No public comment threads on individual findings (lead submission ≠ comment).
- No automated retractions or silent edits.
- No expansion to private individuals; the publication threshold (`legal-guardrails.md`) is fixed.
