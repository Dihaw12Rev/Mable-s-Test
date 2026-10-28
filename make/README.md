# MTMC ⇄ Nuance sync: Make.com blueprints v2

Rebuilt versions of the MTMC ⇄ Nuance sync scenarios, built on the **live** scenarios in the MTMC Health Make organization (pulled 2026-10-26). Goals:
- the sync does everything the **MTMC Sync Guide** describes;
- it includes the two changes Nuance approved (company matching with a **domain step**, and **append-only** contact fill);
- it runs on a **1-hour** handoff cycle;
- it closes the timing and duplicate gaps found in review.

No live scenario has been changed. Each v2 scenario is created as a **new, inactive** scenario next to the original, so the original keeps running until we switch over.

**Phase 1 status: LIVE since 2026-10-28** (folder "MTMC to Nuance Sync"):

| Scenario | ID | Built from | Trigger |
|---|---|---|---|
| MTMC <> Nuance – Create Deals from MTMC to Nuance v2 (Phase 1) | 6811855 | `dist/phase1/2_…_phase1_TEST_HOOK` | Webhook 2994157. The MTMC HubSpot workflow now calls this URL. |
| MTMC <> Nuance – Backfill Companies and Contacts to Nuance v2 (Phase 1) | 6811938 | `dist/phase1/6_…_phase1` | Every 3 h, 06:00–19:00 |

The originals are off and moved to the ARCHIVED folder:
- Create Deals (READY): 5904636, webhook 2675167;
- Backfill Companies and Contacts: 6449806.

**Rollback:**
1. Point the MTMC HubSpot workflow back at `https://hook.us2.make.com/44g08bvgc9m3u1s4mgmz6j0ob9hebivo`.
2. Turn the two originals back on.
3. Turn the two v2 scenarios off.

Never run both backfills at the same time.

**Phase 2 status (created 2026-10-28, folder "MTMC to Nuance Sync", all inactive, originals still running):**

| New scenario | ID | Replaces (live) | Trigger |
|---|---|---|---|
| Nuance Deal → MTMC (Create + Update) v2 (Phase 2) | 6813004 | 5563815 | **LIVE since 2026-10-28** (original off, ARCHIVED). Every 1 h; shares watermark `nuance_handoff`. The MTMC Sync copy gets the original deal's owner, contacts and companies (primary label kept). |
| MTMC Deal Updated → Nuance (Update) v2 (Phase 2) | 6812939 | 5563819 | **LIVE since 2026-10-28** (original off, ARCHIVED). Webhook 2994549 (`…/lxywn1ub3v86hbnatvyddgxkrpm8rhxf`); the MTMC workflow points here. |
| MTMC Notes → Nuance (Create + Update) v2 (Phase 2) | 6812950 | 6056956 | **LIVE since 2026-10-28** (original off, ARCHIVED). Every 1 h (was 6 h). |
| Nuance Notes → MTMC (Create + Update) v2 (Phase 2) | 6812969 | 6056834 | **LIVE since 2026-10-28** (original off, ARCHIVED). Every 1 h; includes notes on MTMC Sync copies. |

Before switching each one:
- **Deal update:** done. The stage map (118696) covers every stage in MTMC's Team Pipeline. Stage 1296904841 no longer exists.
- **Notes:** done. The 17 note pairs from the original history (181066; 181067 was empty) were copied into 138595 as `nuance:<id>` / `mtmc:<id>`.
  The data structure of 138595 (473458) now includes `origin`, `nuance_note_id`, `mtmc_note_id`, `source_modified_at` and `last_synced_at`.
  The `mtmc_notes` / `nuance_notes` watermarks were set so the first run starts at the originals' last run (2026-10-28 18:01:35 UTC).
- **Nuance → MTMC notes** copies notes from both Cryodose (31457678) and MTMC Sync (915661656) deals (agreed 2026-10-28).

| File in `dist/` | Replaces (live scenario) | Trigger |
|---|---|---|
| `1_nuance_deal_to_mtmc_v2` | Nuance Deal to MTMC Sync (Create and Update) READY | Schedule, **every 1 h** (was 3 h) |
| `2_mtmc_deal_create_to_nuance_v2` | MTMC <> Nuance – Create Deals from MTMC to Nuance (READY) | Existing webhook 2675167 (instant) |
| `3_mtmc_deal_update_to_nuance_v2` | MTMC Deal Updated → Nuance (Update) | Existing webhook 2738415 (instant) |
| `4_mtmc_notes_to_nuance_v2` | MTMC > Nuance – Notes Sync (Create and Update) (Ready) | Schedule, every 1 h (was 6 h) |
| `5_nuance_notes_to_mtmc_v2` | Nuance > MTMC – Notes Sync (Create and Update) (Ready) | Schedule, every 1 h (was 6 h) |
| `6_mtmc_backfill_companies_contacts_to_nuance_v2` | MTMC <> Nuance – Backfill Companies and Contacts to Nuance | Schedule, every 3 h, 06:00–19:00 (unchanged) |

**Not replaced, and they work alongside v2:**
- "MTMC <> Nuance – Backfill Line Items to Nuance";
- "Nuance – MTMC Team Update";
- "MTMC – Shared Team Update".

**What's in this folder:**
- `original/` — the live blueprints these were built from.
- `build.py` — generates `dist/` from them.
- `code/` — the JavaScript for the Code modules, unit-tested by `test_code.js`.
- `validate.py` — checks the wiring: module IDs, references, numeric settings and that the code parses.

Run all three after any change:

```bash
python3 make/build.py && python3 make/validate.py && node make/test_code.js
```

The changed modules were also validated with Make's own module validator against the live MTMC and Nuance connections. That check also confirms every HubSpot property the blueprints write exists in the right portal.

---

## The two changes Nuance approved

### 1. Company matching includes a domain step (MTMC → Nuance)
It applies in **both** places that bring companies into Nuance: scenario 2 (new MTMC deals) and scenario 6 (backfill). The backfill used to match by exact name and then **overwrite** the matched company with MTMC's name, domain and address.

How a company is matched:
1. **Domain match.** The domain comes from the company's domain or website, ignoring `https://`, `www.` and paths.
   - If **one** Nuance company has that domain, it's used.
   - If **several** share it (for example, facilities of one health system), the one whose **name also matches** wins. Otherwise the oldest record wins.
2. **Name match.** If no domain matches, the names are compared ignoring case, punctuation and Inc / LLC / P.C. style suffixes.
3. **No match:** a new company is created with MTMC's name, domain and address.

Existing companies are **never overwritten**. Only fields that are **blank** on our record (domain, address, city, state, zip, country) are filled from MTMC.

The Nuance → MTMC direction (scenario 1) already matched by domain first. It now uses the same shared-domain and name rules, and never edits MTMC's companies.

### 2. Contact data fill: append only, never overwrite (MTMC → Nuance)
It applies in scenario 2 and scenario 6. The backfill used to overwrite first name, last name, phone and job title on every match.
- Contacts are matched **by email**.
- **New** contacts are created with everything MTMC has.
- **Existing** contacts only get the fields that are **blank** on our side. Anything we already have stays as it is.
- Existing contacts with nothing to fill aren't updated at all, but they're still linked to the deal (and to the company, in the backfill).
- Contacts without an email are skipped, because they can't be matched.

This is the default in the code (`fillBlanksOnly`). Setting it to `false` on the module brings back overwriting, if Nuance ever asks for it.

The Nuance → MTMC direction (scenario 1) already leaves existing MTMC contacts untouched.

---

## Timing

| Flow | Live today | v2 | Worst-case delay |
|---|---|---|---|
| Handoff (Ready for MTMC → MTMC deal, contacts, company, notes) | every 3 h | **every 1 h** | ~1 h. Contacts, company and notes arrive in the **same run** as the deal. |
| Edits to a handed-off deal → MTMC | every 3 h | every 1 h | ~1 h |
| New self-sourced MTMC deal → MTMC Sync | instant (2-min pause) | unchanged | ~2–3 min |
| MTMC deal updates → MTMC Sync | instant | unchanged | < 1 min |
| Notes, both ways (new **and edited**) | every 6 h, new notes only | every 1 h, new and edited | ~1 h. Notes that already exist when a deal is first created are copied with the deal. |
| Missing company / contacts safety net | every 3 h, 06:00–19:00 | unchanged | ≤ 3 h |

**Why 1 hour works:**
- Each scheduled run remembers when the previous one started (`sync_watermarks`).
- It looks for changes since then, minus a short overlap: 30 minutes for deals, 60 for notes. A slow or skipped run never drops anything.
- A handoff that failed is retried on every run until it reaches MTMC, so an edit or a stuck deal can't fall through a gap between runs.
- Duplicates are prevented by the MTMC Deal ID (deals) and the note map (notes). The overlap therefore costs a few credits, never a duplicate record.

**Interactions checked:**
- "Nuance – MTMC Team Update" looks at MTMC Sync deals created in the last 3 hours, every 2 hours. That still catches every new deal.
- "MTMC – Shared Team Update" is webhook-driven, so it's unaffected.

**Credit cost.** Each scheduled run costs about 3 credits when there's nothing to do. Per month, when nothing is happening:

| Scenario | Live today | v2 |
|---|---|---|
| Scenario 1 (handoff) | ~240 | ~2,200 |
| Notes scenarios (both together) | ~240 | ~4,300 |

The notes increase is the price of hourly notes with edits. Every 2 hours halves it, at the cost of up to 2 h of delay. For comparison, the five live scenarios used about 5,600 credits in the last 30 days, by Make's operation counts.

---

## What else changed vs. the live scenarios

### 1. Nuance deal → MTMC (live version unchanged since Oct 16)
- **Stuck handoffs retry automatically.** Any Cryodose deal in *Ready for MTMC* without an MTMC Deal ID is picked up, as long as it entered the stage on or after `HANDOFF_CUTOFF`.
- **No duplicates from partial failures.** The MTMC Deal ID is written back right after the MTMC deal is created, before the line item, the MTMC Sync copy, the Nuance Deal ID write-back and the supplier link. Every step after the create retries if it fails.
- **Contacts, company and notes run on separate paths,** so an empty or failed step can't block the others. In the live version, a deal with no contacts (or with contacts already at MTMC) could stop before the MTMC Sync copy was made.
- **Company:** a blank domain can no longer attach a random MTMC company. When nothing matches, the *Company Creation Requests* ticket is actually created; the live version very likely never reaches that step.
- **Notes:** every note already on the deal is copied to MTMC at handoff.

### 2. MTMC new deal → Nuance (includes today's live change)
- **Target Product = Cryodose TA,** added to the live version today, is kept.
- **Duplicate guard:** deals that already have a Nuance Deal ID, or were created by our handoff, are skipped. The supplier check looks at **all** suppliers, not just the first.
- **MTMC Team:** uses the ZIP-based team when MTMC has assigned one, and otherwise the deal owner's team (see the decisions below).
- **Line items:** only **Nuance Medical** line items are copied, matching the line-item backfill. The live version copies every line item on the deal. The SKU is copied too.
- **Contacts, company and notes:** as described above. Notes that already exist on the MTMC deal are copied when the deal is created.

### 3. MTMC deal update → Nuance (includes the live GPO and Closed Lost Reason fix)
- **Also sends Lead Source.** The live version still doesn't.
- **Stage** is read from the deal, not the webhook payload. Blank values are skipped, so they never wipe our data.
- **MTMC Team** follows the same ZIP-team-first rule, so it no longer overwrites what the team scenarios set.
- Failures are retried instead of silently ignored.

### 4 & 5. Notes
- One note map covers both directions, so edits are carried across and copies are never echoed back.
- **This fixes a live bug in "MTMC > Nuance – Notes Sync":** its edit step sends the MTMC note ID to Nuance's HubSpot and labels the note "Nuance Team".
- Notes are picked up by **last-modified** time, so edits sync. The live versions only see notes created in the last 7 hours.
- "Rep Name" is the note's author, falling back to the deal owner.

### 6. Backfill companies and contacts (safety net)
- The same company and contact rules as above: domain first, never overwrite, fill blanks only.
- Contacts are linked to the deal and to its company, as before.
- What it picks up hasn't changed: MTMC Sync deals with no company, not yet backfilled.

### Fixes from the Make validator
- Retry handlers use numeric attempts and interval.
- Search and list limits are numbers.
- `validate.py` now blocks both mistakes.

---

## Setup (about 30–45 minutes)

1. **Notes data store.** *"Nuance <> MTMC – Notes Sync"* (ID 138595) is empty and unused. Replace its structure fields with:
   - `origin` (text)
   - `nuance_note_id` (text)
   - `mtmc_note_id` (text)
   - `source_modified_at` (date)
   - `last_synced_at` (date)
2. **Stage mapping.** Both deal scenarios use the data store *"Deal Stage Mapping (MTMC <> Nuance)"* (key = MTMC stage ID, value = `Nuanca Deal ID`). It has 6 stages today, and **MTMC stage 1296904841 isn't mapped**. Check it against the "Deal Stage Sync" Google Sheet that live scenario 2 uses. Unmapped stages fall back to the MTMC Sync starting stage on create, and are left unchanged on update.
3. **Import** each blueprint into the *MTMC to Nuance Sync* folder. Each one starts **off**.
4. **Set the schedules:**
   - scenario 1: every 60 min;
   - scenarios 4 and 5: every 60 min;
   - scenario 6: every 3 h, 06:00–19:00.

   Scenarios 2 and 3 are webhook-driven.
5. **Settings.** *Allow storing of incomplete executions* is on in the blueprints, so failed steps are retried and kept. It's off on all the live scenarios.
6. **Switchover.** For each pair: turn the old scenario off, move the webhook (scenarios 2 and 3), then turn the new one on.
   - **Notes:** turn the old notes scenarios off and wait one cycle before turning 4 and 5 on. Their first run only looks back 1 hour, so already-copied notes aren't copied again.
7. **Error alerts.** In *Profile → Notifications*, turn on email alerts for errors and incomplete executions, for the sync owners.
8. **Backfill cutoff (optional).** To send older Ready-for-MTMC deals that never reached MTMC, lower `HANDOFF_CUTOFF` in `build.py` and rebuild.

### Decisions to confirm with Nuance / MTMC
- **Line items:** copy only Nuance Medical line items (v2, same as the line-item backfill), or every line item on the deal (live)?
- **MTMC Team:** the ZIP-based team when MTMC has one, otherwise the deal owner's team (v2)? Today the update scenario and the team scenarios overwrite each other.
- **Notes schedule:** hourly (about 4,300 idle credits a month) or every 2 hours (about 2,200)?
- **Last Activity Date** (optional): create a Nuance deal date property, then set `lastActivityProperty` on Code module 401 in scenario 3. MTMC's `notes_last_updated` then syncs to it.

---

## Guide → automation checklist

| Guide says | Where it happens (scenario · module) |
|---|---|
| Ready for MTMC in Cryodose triggers the handoff (now every **1 h**) | 1 · search 12 (schedule set in Make) |
| MTMC deal in Nuance pipeline / Started Discovery with name, amount, close date, rep name and email, zip | 1 · 18 |
| One Cryodose TA line item, qty 1, price = amount | 1 · 84 |
| Contacts matched by email; existing kept; new created with name, phone, title | 1 · 201–209 |
| Company matched by domain; otherwise a Company Creation Requests ticket | 1 · 211–218, 77 |
| Write-back: MTMC Deal ID + Last Synced At | 1 · 23 |
| Linked MTMC Sync copy (name, amount, close date, owner, MTMC Deal ID, Cryodose TA, source = Nuance) | 1 · 64, 65 |
| Later edits update MTMC, except stage and close date | 1 · 87, 86 |
| Deal notes go to MTMC | 1 · 221–230 (at handoff), 5 (ongoing) |
| Self-sourced deals with Nuance Medical supplier → MTMC Sync, source = MTMC, Target Product = Cryodose TA | 2 · 7, 6, 14 |
| Stage via mapping table; amount, close date, closed lost reason, distributor, GPO, lead source | 2 · 36, 14 · 3 · 36, 401 |
| MTMC rep name, email, team | 2 · 14 · 3 · 401 |
| **Contacts by email: created if new; existing only get blank fields filled** | 2 · 311–319, 341–342 · 6 · 621–643 |
| **Company by domain, then name; else created with MTMC's details; never overwritten** | 2 · 321–329, 343 · 6 · 601–613 |
| MTMC line items → new line items (name, qty, price, USD) | 2 · 8, 301–303, 16 |
| No Nuance owner on self-sourced deals | 2 · 14 (owner not set) |
| MTMC notes → MTMC Sync deal | 2 · 331–340 (at creation), 4 (ongoing) |

### Guide text to update once v2 is live
- **Timing:** "every 3 hours" becomes "every hour" (Sync timing table, Team guidance step 8, Troubleshooting).
- **Companies coming back:** matched by **domain first, then name**. Our existing company records are never overwritten, only blank fields are filled. The duplicate-company row becomes rare.
- **Contacts coming back:** existing contacts only get **blank fields filled**. Change the "Contact details changed on their own" troubleshooting row.
- **Duplicates:** moving a deal in and out of Ready for MTMC doesn't duplicate it, and a deal that didn't arrive is retried automatically.
- **Notes:** sync both ways within about an hour, including edits. Notes logged before the handoff go with the deal, and notes on the MTMC Sync copy also go to MTMC.
- **Owners:** handed-off MTMC Sync deals keep the Nuance owner. Only self-sourced ones are unowned.
- **Errors:** they're stored in Make's *Incomplete executions* and emailed to the sync owners.

---

## Test plan (run in order, with test records)

1. **Handoff, full:** a deal with a company (with domain), 2 contacts (one already at MTMC), 2 notes and a postal code. Move it to Ready for MTMC and run scenario 1 once. Expect:
   - one MTMC deal, one line item and one company linked;
   - one new contact plus one existing contact linked;
   - 2 notes at MTMC;
   - the MTMC Sync copy;
   - both IDs written back;
   - scenario 2 skipping it (check its history).
2. **Handoff edge cases:**
   - no contacts;
   - a company with no domain and no MTMC match (expect a ticket);
   - a company that matches only by name.
3. **Re-run scenario 1:** no new MTMC deal; the update path runs only if the deal was edited.
4. **Edit after handoff:** change amount, name and close date. Within the hour, amount and name change at MTMC; close date doesn't.
5. **Self-sourced, append-only checks.** Create an MTMC deal with:
   - the Nuance Medical supplier;
   - one Nuance line item and one line item from another vendor;
   - a contact that exists at Nuance with a **different** phone and a **blank** job title at Nuance;
   - a company whose name differs from ours but whose **domain matches**;
   - a note.

   Expect:
   - one MTMC Sync deal (source = MTMC, Target Product = Cryodose TA);
   - **only the Nuance line item**;
   - the contact's **phone unchanged** and **job title filled**;
   - **our existing company linked, not renamed, no duplicate**;
   - the note copied.
6. **Shared domain:** two Nuance companies with the same domain. The one whose name matches is linked.
7. **MTMC update:** change stage, Closed Lost Reason, GPO, Lead Source and owner. Expect all of them on our MTMC Sync deal within a minute, and MTMC Team unchanged when a ZIP team is set.
8. **Backfill:** an MTMC Sync deal with no company. On the next backfill run, the company is linked by domain and contacts are added with blanks filled only.
9. **Notes, both ways:** add and then edit a note on each side. Expect exactly one copy each way, the edit carried over, and no echo back.
10. **Failure:** temporarily point a module at a bad property. Confirm the run lands in *Incomplete executions* and an alert email arrives.
