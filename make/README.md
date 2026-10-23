# MTMC ⇄ Nuance sync: Make.com blueprints v2

Rebuilt versions of the four MTMC sync scenarios, plus a fifth for Nuance → MTMC notes. The goal is for the sync to do everything the **MTMC Sync Guide** describes, and to close the timing and duplicate gaps found in review.

| File in `dist/` | Replaces | Trigger |
|---|---|---|
| `1_nuance_deal_to_mtmc_v2` | Nuance Deal to MTMC Sync (Create and Update) | Schedule, every 3 h |
| `2_mtmc_deal_create_to_nuance_v2` | MTMC <> Nuance – Create Deals from MTMC to Nuance | Existing webhook (instant) |
| `3_mtmc_deal_update_to_nuance_v2` | MTMC Deal Updated → Nuance (Update) | Existing webhook (instant) |
| `4_mtmc_notes_to_nuance_v2` | MTMC > Nuance – Notes Sync | Schedule, every 15 min |
| `5_nuance_notes_to_mtmc_v2` | The Nuance → MTMC notes automation (not shared; this replaces it) | Schedule, every 15 min |

`original/` holds the exports these were built from. `build.py` generates `dist/` from them. `code/` holds the JavaScript for the Code modules, which `test_code.js` unit-tests. `validate.py` checks the wiring. Run all three after any change:

```bash
python3 make/build.py && python3 make/validate.py && node make/test_code.js
```

> **Note:** The live scenarios already have some fixes made after these exports (the Closed Lost Reason, GPO and Lead Source updates, the company ticket, and the notes data store). v2 makes the same fixes independently, so compare before overwriting anything.

---

## Setup (about 30 minutes)

1. **Notes data store.** In *Data stores → "Nuance <> MTMC – Notes Sync"* (ID 138595), add these fields to its data structure:
   - `origin` (text)
   - `nuance_note_id` (text)
   - `mtmc_note_id` (text)
   - `source_modified_at` (date)
   - `last_synced_at` (date)

   Existing records are untouched. New records use the keys `nuance:<note id>` and `mtmc:<note id>`.
2. **Stage mapping.** Both deal scenarios now read the data store *"Deal Stage Mapping (MTMC <> Nuance)"* (key = MTMC stage ID, value = `Nuanca Deal ID`). Make sure it has every row that is in the "Deal Stage Sync" Google Sheet. The sheet is no longer used. Unmapped stages fall back to the MTMC Sync starting stage on create, and are left unchanged on update.
3. **Import.** For each scenario: *Create a new scenario → ⋯ → Import Blueprint*. Then open any module that shows a warning and re-select its connection or data store. IDs carry over when they're in the same Make team. Blueprints don't carry a schedule, so set it in Make: scenario 1 every 3 hours, scenarios 4 and 5 every 15 minutes.
4. **Scenario settings.** In each scenario's settings, check that *Allow storing of incomplete executions* is **on** (the blueprints set it). Webhook scenarios 2 and 3 also have *Sequential processing* on.
5. **Webhooks.** Scenarios 2 and 3 reuse the existing hooks (`2675167`, `2738415`). Switch the old scenarios **off** before switching the new ones on, so only one scenario listens to each hook.
6. **Notes switchover.** This avoids duplicate notes:
   - Turn the old notes scenarios **off** (both directions).
   - Wait for one more cycle of the old schedule, then turn on 4 and 5.
   - On their first run, 4 and 5 only look back 1 hour.
7. **Error alerts.** In *Profile → Notifications*, turn on email alerts for errors and for incomplete executions, for whoever owns the sync (RevGravy and Sales Ops). Failed runs now land in *Incomplete executions* instead of disappearing.
8. **Backfill cutoff (optional).** Scenario 1 only auto-sends deals that entered *Ready for MTMC* on or after `HANDOFF_CUTOFF` (2026-10-23). To pick up older deals that never reached MTMC, first list them in HubSpot (Cryodose pipeline, Ready for MTMC, MTMC Deal ID unknown). Then lower the date in `build.py` and rebuild.

### Assumptions to confirm
- These internal names exist as used:
  - on Nuance: `distributor`, `gpo`, `lead_source`, `closed_lost_reason`;
  - on MTMC: `distributor_name`, `gpo`, `source`.

  Enumeration values must match between the portals, or HubSpot rejects the update.
- The MTMC workflow that calls webhook 2 can still fire on handed-off deals. That's fine now, because scenario 2 skips any deal with `nuance_deal_id` or `nuance_last_synced_at`.
- **Last Activity Date** (optional): create a Nuance deal date property, e.g. `mtmc_last_activity_date`. Then set `lastActivityProperty` on Code module 401 in scenario 3 to that name, and it starts syncing MTMC's `notes_last_updated`.
- **Contact overwrites:** set `fillBlanksOnly` to `true` on Code module 315 in scenario 2 and MTMC only fills empty fields on our contacts. The guide currently says to overwrite, so it ships as `false`.

---

## What changed, and why

### 1. Nuance deal → MTMC
- **Stuck handoffs retry automatically.** The search picks up any Cryodose deal in *Ready for MTMC* that has no MTMC Deal ID, not only deals that entered the stage in the last 4 hours. The update window is measured from the last successful run (saved in `sync_watermarks`), so a paused or failed run no longer drops deals.
- **No duplicates from partial failures.** The MTMC Deal ID is written back **immediately** after the MTMC deal is created. Then come, in order:
  - the line item;
  - the MTMC Sync copy;
  - the Nuance Deal ID on the MTMC deal;
  - the supplier association.

  Every step after the create retries automatically if it fails.
- **Contacts, company and notes run independently** (on separate router paths), so a deal with no contacts, or with contacts that all already exist, still gets its company, notes and MTMC Sync copy.
  - *Contacts:* looked up at MTMC by email. Existing contacts are only linked, never changed. New contacts are created already linked to the deal. No empty batch calls.
  - *Company:* the deal's **primary** company is matched at MTMC by **exact domain** (taken from domain or website, ignoring `https://` and `www.`), then by exact name. Exactly one company is linked. A blank domain can no longer attach a random company. No match → the *Company Creation Requests* ticket, which now always fires and has state, country and the Nuance IDs in the description.
  - *Notes:* **every note already on the deal** is copied to the MTMC deal at handoff. This removes the timing gap for notes logged before the deal was moved.
- The update path is unchanged in scope (name, amount, rep, zip; never stage or close date). Errors now retry instead of being silently ignored.

### 2. MTMC new deal → Nuance
- **Duplicate guard:** skips deals that already have a Nuance Deal ID, or that were created by our handoff (`nuance_last_synced_at` is set).
- **Supplier check** looks at *all* of the deal's suppliers, not just the first.
- The Nuance Deal ID is written back to MTMC immediately after create.
- **Line items, contacts, company and notes** run on separate router paths, so a deal without line items still gets its contacts and company.
  - *Contacts:* batch **upsert by email**, matching the guide. Blank MTMC values never erase ours. Contacts without an email are skipped instead of erroring.
  - *Company:* **domain first, then exact name**, as proposed in the guide's open question. A new company is only created when neither matches, with MTMC's name and domain.
  - *Notes:* every note already on the MTMC deal is copied to the new MTMC Sync deal.
- Stage comes from the shared stage-mapping data store, with a fallback stage, so a missing mapping can't block creation.

### 3. MTMC deal update → Nuance
- Sends **all guide fields**: stage (mapped), amount, close date, **Closed Lost Reason, Distributor, GPO, Lead Source**, and the MTMC rep's name, email and primary team.
- Stage is read from the deal itself, not the webhook payload. Blank values are left out, so they never wipe our data.
- Only runs for deals linked to a Nuance deal. Failures retry instead of being ignored.

### 4 & 5. Notes, both directions
- One data store records every note pair in **both** directions. That means:
  - no duplicates;
  - edits are carried across;
  - copies are never echoed back (`origin` check, plus the `[Note from … Team` prefix as a second guard).
- Notes are scanned **by last-modified time since the last run**, so edits sync and nothing is lost if a run is skipped.
- A note syncs when it's on **any** linked deal. Nuance → MTMC includes the Cryodose and MTMC Sync pipelines, which answers the guide's question about notes logged on the MTMC Sync copy.
- "Rep Name" is the **note's author**, falling back to the deal owner.
- Notes on deals that aren't synced yet are no longer a timing risk: the deal-creation scenarios copy all existing notes when the deal is first created.

---

## Guide → automation checklist

| Guide says | Where it happens (scenario · module) |
|---|---|
| Ready for MTMC in Cryodose triggers the handoff, every 3 h | 1 · search 12 (schedule set in Make) |
| MTMC deal in Nuance pipeline / Started Discovery with name, amount, close date, rep name and email, zip | 1 · 18 |
| One Cryodose TA line item, qty 1, price = amount | 1 · 84 |
| Contacts matched by email; existing kept; new created with name, phone, title | 1 · 201–209 |
| Company matched by domain; otherwise a Company Creation Requests ticket | 1 · 211–218, 77 |
| Write-back: MTMC Deal ID + Last Synced At | 1 · 23 |
| Linked MTMC Sync copy (name, amount, close date, owner, MTMC Deal ID, Cryodose TA, source = Nuance) | 1 · 64, 65 |
| Later edits update MTMC, except stage and close date | 1 · 87, 86 |
| Deal notes go to MTMC | 1 · 221–230 (at handoff), 5 (ongoing) |
| Self-sourced deals with Nuance Medical supplier → MTMC Sync, source = MTMC | 2 · 7, 6, 14 |
| Stage via mapping table; amount, close date, closed lost reason, distributor, GPO, lead source | 2 · 36, 14 · 3 · 36, 401 |
| MTMC rep name, email, team | 2 · 14 · 3 · 401 |
| Contacts by email: created if new, updated if existing | 2 · 311–318 |
| Company by exact name; else created with MTMC's domain (now domain first) | 2 · 321–329 |
| MTMC line items → new line items (name, qty, price, USD) | 2 · 8, 301–16 |
| No Nuance owner on self-sourced deals | 2 · 14 (owner not set) |
| MTMC notes → MTMC Sync deal | 2 · 331–340 (at creation), 4 (ongoing) |

### Guide text to update once v2 is live
- Companies coming back match **by domain first, then exact name**, so the duplicate-company troubleshooting row is now rare.
- Moving a deal in and out of Ready for MTMC doesn't duplicate it. A deal that didn't arrive is retried automatically on the next run.
- Notes sync both ways within about 15 minutes, including edits. Notes logged before the handoff are sent when the deal is handed off. Notes on the MTMC Sync copy also go to MTMC.
- Handed-off MTMC Sync deals keep the Nuance owner. Only self-sourced ones are unowned.
- Errors are stored in Make's *Incomplete executions* and emailed to the sync owners.

---

## Test plan (run in order, with test records)

1. **Handoff, full:** a deal with a company (with domain), 2 contacts (one already at MTMC), 2 notes and a postal code. Move it to Ready for MTMC and run scenario 1 once. Expect:
   - one MTMC deal and one line item;
   - one company linked;
   - one new contact plus one existing contact linked;
   - 2 notes at MTMC;
   - the MTMC Sync copy;
   - both IDs written back;
   - scenario 2 skipping it (check its history).
2. **Handoff, edge cases:**
   - a deal with no contacts;
   - one whose company has no domain and no match at MTMC (expect a ticket);
   - one whose company matches only by name.
3. **Re-run scenario 1:** no new MTMC deal; the update path runs only if the deal was edited.
4. **Edit after handoff:** change amount, name and close date on the Cryodose deal. On the next run, amount and name change at MTMC; close date doesn't.
5. **Self-sourced:** create an MTMC deal with the Nuance Medical supplier, a line item, a contact that exists at Nuance with a different phone, a company whose name differs but domain matches, and a note. Expect:
   - one MTMC Sync deal with source = MTMC;
   - the line item;
   - the contact updated;
   - the existing company linked (no duplicate);
   - the note copied.
6. **MTMC update:** change stage, Closed Lost Reason, GPO and owner at MTMC. Expect all of them on our MTMC Sync deal within a minute.
7. **Notes, both ways:** add and then edit a note on each side. Expect exactly one copy each way, the edit carried over, and no echo back.
8. **Failure:** temporarily point a module at a bad property and confirm the run lands in *Incomplete executions* and an alert email arrives.
