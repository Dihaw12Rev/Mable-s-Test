# RevGravy Portal Assessment Rubric v1.0

The rubric is the product. It turns raw portal data into consistent, defensible grades
so two architects auditing the same portal reach the same conclusions. Every check
defines: **what is measured**, **where the data comes from**, and **thresholds** for
Pass / Warn / Fail.

## Scoring model

- Each **check** scores 100 (Pass), 50 (Warn), or 0 (Fail). Checks marked `[info]` are
  reported but not scored.
- Each **pillar score** = weighted average of its checks (weights below, sum to 100 per pillar).
- **Portal score** = weighted average of pillars.
- Letter grades: A ≥ 90 · B ≥ 75 · C ≥ 60 · D ≥ 45 · F < 45.
- Every Fail/Warn finding must carry: severity (pillar weight × check weight), the
  fix-skill slug that resolves it, and the RevGravy SKU from `services/catalog.yaml`.

## Pillar weights

| Pillar | Weight |
|---|---|
| 1. Data Hygiene | 25% |
| 2. Automation Health | 20% |
| 3. Pipeline & Sales Process | 20% |
| 4. Reporting & Attribution | 15% |
| 5. Adoption & Governance | 20% |

---

## Pillar 1 — Data Hygiene (25%)

| # | Check | Source | Pass | Warn | Fail | Wt |
|---|---|---|---|---|---|---|
| 1.1 | Contacts with no email | CRM search: `email` unknown | <2% | 2–8% | >8% | 15 |
| 1.2 | Hard-bounced contacts not suppressed | `hs_email_hard_bounce_reason` known AND marketing contact | <0.5% | 0.5–2% | >2% | 15 |
| 1.3 | Duplicate companies (domain match) | Companies grouped by `domain` | <1% | 1–5% | >5% | 15 |
| 1.4 | Unowned contacts (marketing contacts, no owner) | `hubspot_owner_id` unknown | <5% | 5–20% | >20% | 10 |
| 1.5 | Key-property fill rate (contacts: firstname, company, lifecycle; companies: industry, domain) | Property completeness query | >85% | 60–85% | <60% | 15 |
| 1.6 | Property sprawl: custom properties with 0 populated values | Properties API + usage query | <10% | 10–30% | >30% | 10 |
| 1.7 | Records owned by deactivated users | Owners API × CRM ownership | 0 | <2% | ≥2% | 10 |
| 1.8 | Ghost contacts (no activity ≥ 12 months, no lifecycle progress) | Last activity date query | <10% | 10–30% | >30% | 10 |

## Pillar 2 — Automation Health (20%)

| # | Check | Source | Pass | Warn | Fail | Wt |
|---|---|---|---|---|---|---|
| 2.1 | Workflows turned off or with 0 enrollments in 90 days | Automation API v4 | <15% | 15–40% | >40% | 20 |
| 2.2 | Workflows with execution errors in last 30 days | Automation API v4 logs | 0 | 1–3 | >3 | 20 |
| 2.3 | Workflows with no description / naming convention | Flow metadata | >80% named | 50–80% | <50% | 10 |
| 2.4 | Forms with 0 submissions in 90 days | Forms API | <25% | 25–50% | >50% | 15 |
| 2.5 | Active lists that haven't changed size in 90 days (stale/dead lists) | Lists API | <20% | 20–50% | >50% | 15 |
| 2.6 | Core hygiene automations exist (bounce suppression, lifecycle progression, new-contact screening) | Flow inventory scan | 3/3 | 1–2/3 | 0/3 | 20 |

## Pillar 3 — Pipeline & Sales Process (20%)

| # | Check | Source | Pass | Warn | Fail | Wt |
|---|---|---|---|---|---|---|
| 3.1 | Open deals with close date in the past | Deals query | <5% | 5–20% | >20% | 20 |
| 3.2 | Open deals with no amount | Deals query | <5% | 5–15% | >15% | 15 |
| 3.3 | Stale deals (no activity ≥ 45 days, open) | Deals + engagement query | <10% | 10–30% | >30% | 20 |
| 3.4 | Deals with no associated contact or company | Associations query | <2% | 2–10% | >10% | 15 |
| 3.5 | Pipeline stage probability configured (not defaults) on primary pipeline | Pipelines API | yes | partial | no | 10 |
| 3.6 | Win rate & average cycle length computable (required properties present) | Closed-deal query | yes | partial | no | 10 |
| 3.7 | Lifecycle stage regressions (customer → lead, etc.) | Lifecycle history sample | <1% | 1–5% | >5% | 10 |

## Pillar 4 — Reporting & Attribution (15%)

| # | Check | Source | Pass | Warn | Fail | Wt |
|---|---|---|---|---|---|---|
| 4.1 | Dashboards viewed in last 30 days | Dashboards/analytics | >50% | 20–50% | <20% | 25 |
| 4.2 | Original source populated on contacts | `hs_analytics_source` | >90% | 70–90% | <70% | 25 |
| 4.3 | Campaigns in active use (assets associated, last 90 days) | Campaigns API | yes | partial | no | 20 |
| 4.4 | Revenue attribution / closed-won source report exists and is populated | Reports scan | yes | partial | no | 20 |
| 4.5 | UTM discipline: % of paid/campaign traffic with UTM data `[info]` | Analytics API | — | — | — | 10 |

## Pillar 5 — Adoption & Governance (20%)

| # | Check | Source | Pass | Warn | Fail | Wt |
|---|---|---|---|---|---|---|
| 5.1 | Paid seats with no login in 30 days | Users/org API | <10% | 10–30% | >30% | 25 |
| 5.2 | Sales activity logging: open deals w/ logged activity in 30 days | Engagements query | >70% | 40–70% | <40% | 20 |
| 5.3 | Naming conventions followed (workflows, lists, properties prefix/date pattern) | Metadata scan | >70% | 40–70% | <40% | 15 |
| 5.4 | Super-admin count proportionate to team size | Users API | ≤3 or ≤10% | — | >10% | 15 |
| 5.5 | Connected integrations healthy (no failing syncs) `[info if API-limited]` | Integrations scan | all | 1 failing | >1 | 15 |
| 5.6 | Teams & permission sets configured (not everyone unrestricted) | Org API | yes | partial | no | 10 |

---

## Output contract

Every audit run must emit `audit/<client-slug>/portal_snapshot.json` with this shape —
both downstream skills consume it:

```json
{
  "client": "acme-co",
  "portal_id": 12345678,
  "run_date": "2026-07-20",
  "pillars": [
    {
      "id": "data-hygiene",
      "score": 62,
      "grade": "C",
      "checks": [
        {
          "id": "1.2",
          "name": "Hard-bounced contacts not suppressed",
          "metric": "3.4%",
          "result": "fail",
          "severity": 3.75,
          "evidence": "4,213 of 123,900 marketing contacts",
          "fix_skill": "suppress-hard-bounced",
          "sku": "RG-HYG-02"
        }
      ]
    }
  ],
  "portal_score": 64,
  "portal_grade": "C"
}
```

## Calibration notes

- Thresholds above are v1 defaults from industry norms — calibrate on the first 3
  pilot audits and version the rubric (clients signed under v1 are re-graded under v1).
- Checks the portal's plan tier makes impossible (e.g., no Marketing Pro → no
  workflows) are excluded and the pillar re-weighted, never scored as Fail.
- Never grade on data the API couldn't fetch — mark `[info] insufficient access`
  and flag the missing scope in the report.
