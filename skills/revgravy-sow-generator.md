---
name: revgravy-sow-generator
description: Turn audit findings into a phased, priced RevGravy Statement of Work by mapping every Fail/Warn finding to a SKU from the services catalog. Use this whenever an assessment or audit exists and the user wants a proposal, quote, SOW, engagement plan, pricing, "what would it cost to fix this", or a client-ready remediation roadmap — even if they only say "send them a plan". Always run this INSTEAD of the generic hubspot-implementation-plan when the output is commercial (for a client) rather than internal (for an admin).
license: MIT
metadata:
  author: RevGravy
  version: 0.1.0
  category: audit-planning
---

# RevGravy SOW Generator

The commercial half of the audit: reads `portal_snapshot.json`, maps findings to SKUs
in `services/catalog.yaml`, sequences them by dependency, and produces a client-ready
SOW with phases, hours, and pricing. The generic implementation plan answers "what do
we fix"; this answers "what do we sell, in what order, for how much".

## Inputs

1. `audit/<client-slug>/portal_snapshot.json` — findings with `sku` fields per RUBRIC.md.
2. `services/catalog.yaml` — SKU → fixes, hours range, rates. If `hourly_rate_usd: 0`
   or any referenced SKU is missing, STOP and ask — never invent prices.
3. `clients/<client-slug>.yaml` — engagement overrides (client-specific rate).
4. Optional: `audit/<client-slug>/assessment.html` — link it in the SOW appendix.

## Stage 1 — Plan

- Confirm scope with the user: full remediation vs. top-priorities-only vs. a target
  grade ("get them to a B"). Default: phased full remediation.
- Confirm commercial model: hourly, fixed-fee per phase, or retainer conversion.
- Surface findings that have **no SKU mapping** — these are catalog gaps. Offer to
  add a SKU to the catalog (mirrors the upstream repo's create-skill-on-the-spot
  pattern, applied to the service catalog).

## Stage 2 — Before

- Aggregate: group Fail/Warn findings by SKU, sum severity per SKU, dedupe (one SKU
  appears once even if it fixes six findings — findings listed under it as evidence).
- Build the dependency graph from SKU category order:
  hygiene → enrichment → segmentation/scoring → automation → reporting → governance →
  maintenance retainer. (You can't score leads before enriching; can't report before
  the data is clean.) Respect explicit `depends_on` fields in the catalog if present.
- Show the user the draft SKU list with hours/prices BEFORE writing the document —
  pricing is a human decision; this skill proposes, the architect disposes.

## Stage 3 — Execute

Write `audit/<client-slug>/sow-YYYY-MM-DD.md` (and offer .docx export) with:

1. **Engagement summary** — current grade, target grade, total investment range,
   total duration estimate.
2. **Phases** (typically 2–4) — each with: objective in business language, SKUs
   included, findings resolved (with evidence metrics from the snapshot), hours range,
   price, expected pillar-score impact ("Data Hygiene: C → A").
3. **Out of scope / assumptions** — plan-tier limits found in the audit, client-side
   responsibilities (approvals, UI access), data the API couldn't reach.
4. **Ongoing maintenance option** — always include the RG-OPS-01 retainer as the
   final section: the audit→fix→maintain funnel is the business model.
5. **Appendix** — link/reference to the full assessment; rubric version.

Rules:
- Every price traces to catalog hours × rate — show the math in an internal
  `sow-worksheet.md` (NOT sent to client) so Phil can review margin.
- Expected score impact is computed by re-running the rubric with the SKU's checks
  set to Pass — never hand-waved.
- Language follows `clients/<slug>.yaml` (`en`/`es`).

## Stage 4 — After

- Sanity check: total hours vs. contacts_approx (a 5k-contact portal should not
  produce an 80-hour hygiene phase — flag anomalies instead of shipping them).
- Diff against any previous SOW for this client to avoid re-selling completed work.
- Offer next steps: export to .docx, draft the cover email, or log to the
  Factory Tracking system.

## Rollback / safety

Read-only against the portal. Writes only to `audit/<client-slug>/`.
Never sends anything to the client — output is always reviewed by the architect first.
