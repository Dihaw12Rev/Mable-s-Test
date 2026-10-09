# HubSpot Portal Documentation

Generates an as-built reference for a HubSpot portal: every workflow, property, list,
form, marketing email, and CMS page — cross-referenced, described in plain language, and
linked back to the asset in HubSpot. Output is an interactive HTML report and a Word
document from the same data.

Every API call is read-only. Nothing in this repository writes to a portal.

## Why this exists

Existing HubSpot tooling (including [`TomGranot/hubspot-admin-skills`][skills], which is
excellent) is built to *find and fix defects* — dedupe contacts, suppress bounces, delete
dead workflows. This is built to *describe what exists*: what each workflow does, which
properties the automation actually depends on, and how the pieces connect.

The core output is the **property usage index**. For every property it resolves which
workflows write it, which read it in enrollment or branch criteria, which forms collect
it, and which lists segment on it. That measured usage — rather than a guess from the
property's name — is what separates a property that matters from one that is merely
present.

[skills]: https://github.com/TomGranot/hubspot-admin-skills

## Setup

1. **Create a private app** in the portal: Settings → Integrations → Private Apps →
   Create private app → Scopes tab. Tick these, all read-only:

   | Scope | Unlocks |
   |---|---|
   | `automation` | Workflows (the v4 Automation API) |
   | `crm.schemas.contacts.read` | Contact properties |
   | `crm.schemas.companies.read` | Company properties |
   | `crm.schemas.deals.read` | Deal properties |
   | `crm.schemas.custom.read` | Custom object properties and schemas |
   | `crm.schemas.line_items.read` | Line item properties |
   | `crm.schemas.quotes.read` | Quote properties |
   | `crm.lists.read` | Lists and their filter criteria |
   | `crm.objects.owners.read` | Owners, including deactivated ones |
   | `forms` | Forms and their field mappings |
   | `marketing-email` | Marketing emails |
   | `content` | Landing pages, site pages, blog posts |
   | `account-info.security.read` | Portal name, time zone, API usage (optional) |

   Every scope above is read-only; the tool never writes. Copy the access token from
   the token tab **after** saving the scopes — HubSpot issues a new token whenever an
   app's scopes change, so a token copied beforehand keeps the old permissions.

   Missing one is not fatal. Any endpoint that 403s is recorded, named in the report's
   coverage section together with the scope names HubSpot itself asked for, and the
   run continues. The console prints the same list, so the usual loop is: run it, read
   what it asks for, tick those, run again.

2. **Store the token.** Copy `.env.example` to `.env` and fill in
   `HUBSPOT_ACCESS_TOKEN`. `.env` is gitignored; the token never appears in any output.

3. **Run it.** No project setup — [`uv`](https://github.com/astral-sh/uv) resolves
   dependencies from the script header:

   ```bash
   uv run run_audit.py
   ```

Missing scopes degrade gracefully: an endpoint that returns 401/403/404 is recorded and
listed in the report's *Coverage & caveats* section rather than aborting the run. A portal
without Marketing Hub still produces a complete workflow and property inventory.

## Output

```
data/snapshot.json     raw API responses, re-renderable without re-fetching
data/analysis.json     the cross-referenced model
reports/hubspot-portal-documentation.html
reports/hubspot-portal-documentation.docx
```

Re-render without hitting the API again:

```bash
uv run run_audit.py --snapshot data/snapshot.json
```

Other flags: `--no-docx`, `--no-html`, `--out DIR`, `--data DIR`.

## Workflow activity (the one manual step)

The API says what a workflow is made of. It says nothing about what the workflow has been
doing — there is no route that returns a run date, and property history names the
enrolment rather than the workflow. That half of the picture lives on the workflow CRM
object, and the only way out of HubSpot is a listing export:

1. **Automation → Workflows**, set the view to *All workflows*.
2. Export, adding these columns: *Last action on*, *Enrolled last 7-days*,
   *Enrolled unique*, *Currently Enrolled*, *Current Issue Count*.
3. Save the file HubSpot emails you as `data/workflow-export.xlsx`.

Any run then picks it up automatically (or pass `--workflow-export PATH`). The merge is
additive and keyed on flow id: it attaches activity to workflows the API already
described, adds any workflow created after the snapshot — flagged, with its steps column
reading *not read* — and marks the ones the export no longer lists as possibly deleted.
Without the file the audit still runs; the staleness phase then falls back to edit dates
and says so in every row.

## What the report contains

| Section | Contents |
|---|---|
| At a glance | Asset counts, active vs. off workflows, unused custom property count |
| Automation systems | Workflows grouped by the job they do, inferred from names and the properties they write |
| Workflow reference | Every workflow: enrollment logic, properties read and written, step breakdown, handoffs to other workflows, editor link |
| Property reference | Sorted by measured usage, filterable by object and by referenced/unused/custom |
| Lists, Forms, Emails, Pages | Name, link, state, and the properties each one touches |
| Coverage & caveats | Endpoints that could not be read, unrecognised action types, and what the data cannot tell you |

## How workflow definitions are read

Definitions come from HubSpot's **v4 Automation API** (`/automation/v4/flows`), fetched in
batches. Rather than parsing against a pinned schema, the analyzer scans each definition
generically: keys known to carry references (`property`, `listId`, `flowId`, and friends)
are read directly, and every remaining string is matched against the portal's own property
names. HubSpot reshapes flow JSON periodically, so this degrades to *finding fewer
references* instead of breaking silently.

Action types are labelled from a best-effort table. Any type ID not in the table is
reported by its raw ID and listed in the caveats section — the report says "unrecognised"
rather than guessing wrong.

## Known limits

- **Enrollment history is not in the API.** `/automation/v3/workflows` returns lifetime
  and current enrolment counts for the whole list; nothing returns a per-workflow run
  date, and every per-workflow performance route 404s under both the v4 and the legacy id.
  Run dates come from the workflow export above, so without that file the report never
  claims a workflow is unused — only that it is turned off.
- **Integration and custom-coded references are invisible.** A property set by a custom
  code action or an external integration will not appear in the usage index.
- **Fuzzy matching is out of scope.** Property references are resolved by exact name match.
- **App URLs are best-effort.** HubSpot changes its UI URL structure occasionally; every
  link is built in `hubspot_audit/links.py`, so a structure change is a one-file fix.

## Layout

```
run_audit.py                  entry point (PEP 723 script header)
hubspot_audit/
  client.py                   auth, pagination, rate limiting, scope degradation
  extract.py                  read-only portal snapshot
  analyze.py                  cross-reference model and property usage index
  workflow_export.py          merges HubSpot's workflow listing export into the snapshot
  links.py                    HubSpot UI deep links
  render.py                   HTML and DOCX renderers
  templates/report.html       the interactive report
tests/
  fixture.py                  synthetic portal shaped like real API payloads
  test_pipeline.py            end-to-end analyze + render checks
```

Run the tests — they need no token and touch no portal:

```bash
uv run tests/test_pipeline.py
```
