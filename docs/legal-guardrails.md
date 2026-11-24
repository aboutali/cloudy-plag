# Legal & Ethical Guardrails (Germany)

The platform operates under German law, principally:

- **§§ 185–187 StGB** — Beleidigung, üble Nachrede, Verleumdung.
- **Persönlichkeitsrecht** (Art. 1 I, 2 I GG) — particularly the right to informational self-determination and protection of social standing.
- **DSGVO / BDSG** — personal data processing, including reviewer accounts and right-of-reply records.
- **§ 51 UrhG** — Zitatrecht; bounds quoting from copyrighted sources.
- **TMG / DDG** — impressum, host responsibility, takedown obligations.

## Operating Principles

### Documentation, not verdict

The platform reports observations. It does not declare plagiarism. Language is enforced via a controlled vocabulary in the UI:

| Allowed                         | Not allowed                |
|---------------------------------|----------------------------|
| "Fundstelle"                    | "Plagiat"                  |
| "ungeklärte Übernahme"          | "Betrug"                   |
| "fehlender Quellennachweis"     | "abgeschrieben"            |
| "ähnlicher Wortlaut zu …"       | "kopiert von …"            |
| "Hinweis auf mögliche …"        | "ist ein/e …"              |

Verdict-language ("Plagiat", "Betrug") is reserved for direct quotes from authorities (university decisions, court rulings) — and then attributed.

### Right of reply

Every documented person has:
- a clearly published contact channel for response,
- the right to publish a statement linked from their page,
- the right to dispute a finding (creates `Finding.status = disputed` with the dispute visible alongside the finding).

### Takedown & correction process

- Public, documented SOP with target response times.
- Every takedown request, decision, and rationale is logged.
- Erroneous findings are not silently deleted: they receive a visible **correction record** and the finding's status changes to `rejected` with the reasoning preserved.
- Counsel review for any finding contested by named legal representation.

### Threshold for publication

Publication is justified only when:
1. The person is a public figure **and**
2. Their academic credentials are part of their public role (elected office, senior public administration, public claims of expertise based on the doctorate, public use of "Dr." in official capacity).

Borderline cases require editor-in-chief sign-off.

### Quoting limits

Side-by-side comparisons must stay within § 51 UrhG: short, purposeful, attributed. Hard rules:

- No full-text mirroring of copyrighted sources.
- Snippets are bounded to what is necessary to substantiate the finding (configurable per detector; default ~3 sentences either side).
- Source full text is never served to the public; only the matched span and minimal context.
- Citation metadata (title, author, identifiers) is always shown.

### No AI-only publication

Hard rule, both for legal defensibility and for trust:

- AI may generate leads.
- A human reviewer (or two, depending on the finding kind — see `evidence-model.md`) must confirm before public display.
- For `weak_method` and `originality_doubt`, an editor-in-chief signs off.

### Data minimization

- Reviewers may operate under pseudonymous handles; verified-identity is required only for issuing `confirmed` status on legally-sensitive findings.
- Personal data of subjects is limited to what is publicly tied to their dissertation and public role.
- Logs strip IPs and identifying metadata after operational windows expire (TBD; legal review needed).

## Reviewer Code of Conduct (sketch)

Reviewers commit to:

1. Inspect primary sources before confirming any finding.
2. Apply the controlled vocabulary; never paraphrase findings into verdicts.
3. Disclose conflicts of interest (political affiliation, professional relationship to the subject).
4. Recuse from cases where independence cannot be maintained.
5. Refrain from public commentary on cases under review.
6. Treat right-of-reply submissions in good faith and on a defined timeline.

Violations are grounds for revoked reviewer status; for editors-in-chief, named-impressum-level liability applies.

## Adversarial Posture

Political actors will attempt to discredit, flood, SLAPP, or co-opt the platform. Threat-model from day one:

- **Rate limiting and abuse detection** on lead submission and account creation.
- **Reviewer protection** — pseudonymity by default; verified identity stored separately and accessible only to a small editorial circle.
- **Legal counsel on retainer** in Germany; defined escalation path.
- **Coordinated-inauthentic-behavior monitoring** on public-facing comment/lead channels.
- **Conflict-of-interest disclosures** for editors-in-chief published openly.

## Hosting

EU-hosted from day one (Hetzner pragmatic default; OVH or Scaleway as alternatives). German-language imprint and DSGVO documentation. Object storage with EU-region locks.
