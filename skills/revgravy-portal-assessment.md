---
name: revgravy-portal-assessment
description: Generate the client-facing RevGravy Portal Audit Assessment — a branded, single-file HTML dashboard scored against the five-pillar rubric. Use this whenever an audit has been run (a portal_snapshot.json exists or /hubspot-audit just finished) and the user wants the client deliverable, mentions "assessment", "audit dashboard", "client report", "portal grade", or asks to present audit findings to a client, even if they don't say "dashboard" explicitly. Always run this INSTEAD of writing an ad-hoc report when the audience is the client rather than an internal admin.
license: MIT
metadata:
  author: RevGravy
  version: 0.1.0
  category: audit-planning
---

# RevGravy Portal Assessment

Converts raw audit output into the sellable deliverable: a branded, single-file HTML
dashboard graded against `RUBRIC.md`. This is the artifact sent to the client — it must
be consistent between clients, evidence-backed, and free of internal jargon.

## Inputs

1. `clients/<client-slug>.yaml` — client config (portal id, plan tier, language).
2. `audit/<client-slug>/portal_snapshot.json` — output of `/hubspot-audit`
   (or the RevGravy extraction script), conforming to the RUBRIC.md output contract.
3. `RUBRIC.md` — pillar weights, thresholds, grade bands. The rubric version used
   must be printed in the dashboard footer.
4. `assets/brand.css` — RevGravy tokens (colors, logo, fonts). If missing, stop and
   ask rather than inventing a palette.

If the snapshot is missing, offer to run the audit first. Never fabricate metrics —
every number on the dashboard must trace to a `checks[].evidence` field.

## Stage 1 — Plan

- Confirm client slug, language (`en`/`es`), and audience (exec summary vs. admin detail —
  default: both, exec first).
- List which rubric checks were excluded due to plan tier or missing API scopes; these
  render as "Not assessed" chips, never as failures.

## Stage 2 — Before

- Validate `portal_snapshot.json` against the output contract (all pillar ids present,
  scores 0–100, every fail/warn has fix_skill + sku + evidence).
- If a previous assessment exists for this client, load it — the dashboard shows
  score deltas per pillar (the re-audit story is the retainer pitch).

## Stage 3 — Execute

Build `audit/<client-slug>/assessment.html` — one self-contained file, no build step,
inline CSS/JS only. Required sections in order:

1. **Header** — client name, portal id (last 4 digits only), run date, rubric version.
2. **Scorecard hero** — overall grade + score, five pillar gauges with letter grades,
   delta vs. previous assessment if available.
3. **Executive summary** — max 5 bullets, written for a non-admin: business impact,
   not API language ("4,200 contacts are hurting your email deliverability", not
   "hard-bounce property populated").
4. **Pillar detail** ×5 — each check as a row: name, metric, Pass/Warn/Fail chip,
   one-line evidence. Fails sorted first by severity.
5. **Top 5 priorities** — highest-severity findings across pillars, each with the
   plain-language fix and its RevGravy SKU name (no internal skill slugs, no prices —
   prices live in the SOW, not the assessment).
6. **Methodology footnote** — what was scanned, read-only access statement, rubric
   version, "Not assessed" list.

Rendering rules:
- All copy generated in the client's configured language.
- No raw property names, API endpoints, or skill slugs in client-visible text.
- Charts: inline SVG only (no CDN dependencies — file must open offline).

## Stage 4 — After

- Open/inspect the HTML; verify every displayed number matches the snapshot JSON.
- Save alongside it `audit/<client-slug>/assessment-summary.md` (the exec summary in
  markdown) for pasting into email/Slack.
- Offer next step: "Generate the SOW from these findings? → /revgravy-sow-generator"

## Rollback / safety

Read-only skill — it writes only to `audit/<client-slug>/`. Never mutates the portal.
Assessments are timestamped, never overwritten: `assessment-YYYY-MM-DD.html`.
