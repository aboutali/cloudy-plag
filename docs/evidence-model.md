# Evidence Model — "Show Your Work"

The single most important subsystem. Every analysis worker must satisfy this contract before its output can leave the review queue.

## The Contract

A `Finding` is publishable only if all of the following hold:

1. **Inspectable artifact.** At least one of:
   - rendered side-by-side comparison of `DocumentSpan` ↔ `SourceSpan`,
   - citation-graph snapshot showing the originality-doubt context,
   - quoted-claim-with-context view tying a rigor critique to its rubric criterion.
2. **Provenance chain.** The finding resolves to an `AnalysisRun` with model id, version, prompt hash, inputs, outputs, and at least one `Review` with decision `confirm`.
3. **Primary-text reachability.** A reader who distrusts the AI must be able to verify the finding from the primary text alone, by clicking through to the original page/bbox in the dissertation and the corresponding locator in the source.
4. **Neutral phrasing.** Display strings come from a controlled vocabulary (see `legal-guardrails.md`).

If any of these fail, the finding stays in the reviewer queue. AI never publishes directly.

## AI Outputs Are Structured Leads, Not Prose

Analysis workers do **not** emit human-readable verdicts. They emit structured leads with explicit slots:

```
{
  kind: "weak_method",
  document_span_id: ...,           // exact passage critiqued
  rubric_criterion: "sample_size", // from a finite list per field
  evidence_quote: "...",           // exact text from the dissertation
  context_quote: "...",            // surrounding methods passage
  suggested_concern: "...",        // model's reasoning, reviewer-only
  detector_id, detector_version,
  prompt_hash
}
```

A rigor critique like "sample size of 12 in §4.2 is insufficient for the claim on p.88" must carry the exact quoted claim, the exact methods passage, and the rubric criterion — all clickable to source. Reviewers compose any human-facing prose; the model does not.

## Confidence as a Category, Not a Percentage

Two categories only:

- **`requires_review`** — leads from analysis workers, not published.
- **`documented`** — confirmed by reviewer(s); published with full evidence chain.

Percentages invite false precision and load-bearing decimal places. They are stored internally for ranking the review queue but never displayed.

## Per-Detector Evidence Requirements

| Detector kind             | Required artifact                                                  | Minimum for `documented` |
|---------------------------|--------------------------------------------------------------------|--------------------------|
| `text_reuse`              | side-by-side with character-aligned highlighting                   | one reviewer confirm     |
| `translation`             | side-by-side, original + dissertation, with translation rendered    | one reviewer confirm     |
| `paraphrase`              | side-by-side + semantic-similarity rationale                       | two reviewer confirms    |
| `ai_generated_suspicion`  | detector signal + corroborating evidence; **never standalone**     | always reviewer-only     |
| `unsupported_claim`       | quoted claim + citation neighborhood snapshot                      | two reviewer confirms    |
| `weak_method`             | rubric criterion + methods passage; **reviewer-only by default**   | editor-in-chief approval |
| `originality_doubt`       | claim + matching prior-art spans + citation graph                  | two reviewer confirms    |

`weak_method` and `originality_doubt` are the most defamation-adjacent. Default to reviewer-only visibility for far longer than plagiarism findings (see `roadmap.md` Phase 3).

## Reviewer Workflow

1. Worker emits structured lead → `Finding(status=unreviewed)`.
2. Triager validates the artifact renders correctly and the lead is plausible. Marks `request_more_evidence`, `reject`, or routes to reviewer.
3. Reviewer inspects primary sources, decides `confirm` / `reject` / `dispute`. Writes rationale.
4. For findings requiring two confirms (see table), a second reviewer repeats step 3.
5. For `weak_method`, an editor-in-chief signs off.
6. Only then does the finding render on the public per-person page.

## Reproducibility

Any displayed claim must be re-runnable. `AnalysisRun` stores enough to replay the model invocation: the exact prompt template, the input span ids, model id and version, and the raw structured output. If a model is deprecated, runs against it are flagged on the public view as "produced under deprecated detector vN" — they are not silently rerun.

## What This Forbids

- Publishing an LLM's free-text opinion as a finding.
- Hiding the prompt or model version from the audit log.
- Displaying confidence as `0.83` or "high".
- Aggregating findings into a person-level "score" (no leaderboard, no traffic-light).
- Silent edits or deletions; corrections are append-only and visible.
