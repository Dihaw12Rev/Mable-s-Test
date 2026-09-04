"""The review plan: phase definitions and the work list behind each one.

One source of truth for both the printed plan and the tracker tabs in the
workbook, so a cohort can never mean one thing in the PDF and another in the
spreadsheet.

Phases are ordered by risk, not by size. Everything reversible and evidence-backed
comes first; the phase that carries real business risk (active workflows nobody has
reviewed) sits in the middle, once the clutter is gone and it can actually be seen.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

SAFE, JUDGE, CARE, NONE = "safe", "judgment", "careful", "process"

AUTO_NAME = re.compile(r"^\s*unnamed workflow", re.I)
LEFTOVER = ("test", "temp", "copy of", "draft", "[old", "delete")


def _age_days(value: Any, now: datetime) -> int | None:
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return max((now - stamp).days, 0)


GLOSSARY = [
    ("Workflow", "HubSpot's automation. “When this happens, do that” — for example, when a "
                 "contact's lifecycle stage becomes Customer, notify the account manager."),
    ("Property (or field)", "A single piece of information stored on a record: Email, Deal "
                            "Stage, Contact owner. Every property has a friendly label and a "
                            "hidden internal name; this audit shows the label."),
    ("Enrolment", "A record entering a workflow because it met the starting conditions. "
                  "“Enrols on Email” means the workflow starts when that field matches."),
    ("Writes / reads", "A workflow writes a property when it sets its value, and reads one "
                       "when it checks the value to decide what to do. Writes are the ones "
                       "that change your data."),
    ("Footprint", "How many other things a change here could reach, counted by following the "
                  "connections. A workflow with a footprint of 400 writes fields that 400 "
                  "other things depend on, directly or further down the chain."),
    ("Turned off", "The workflow exists and still holds its logic, but is not enrolling "
                   "anyone right now. It is dormant, not deleted."),
    ("List", "A saved group of records. Active lists update themselves as records change; "
             "static lists are a fixed snapshot from when they were made."),
    ("Suppression list", "A list of people a workflow deliberately skips — usually those who "
                         "have opted out. Deleting one by mistake can start emailing people "
                         "who asked you not to."),
]


def cohorts(analysis: dict[str, Any], g) -> dict[str, list[dict[str, Any]]]:
    """The actual rows of work behind each phase, in the order they should be done."""
    measured = (analysis.get("usage") or {}).get("properties") or {}
    now = datetime.now(timezone.utc)
    workflows = analysis["workflows"]
    reach = {w["id"]: len(g.downstream(f"wf:{w['id']}", 4)) for w in workflows}

    def row(w, **extra):
        base = {
            "name": w["name"],
            "does": w.get("steps_text") or [w.get("description", "")],
            "their_note": w.get("hubspot_description") or "",
            "status": "Active" if w["enabled"] else "Turned off",
            "steps": w["action_count"],
            "updated": str(w["updated_at"] or "")[:10],
            "footprint": reach[w["id"]],
            "writes": w.get("properties_written_labels") or [],
            "link": w["link"],
        }
        base.update(extra)
        return base

    empty = [w for w in workflows
             if not w["action_count"] and not w["properties_written"] and not w["properties_read"]]
    leftover = [w for w in workflows
                if any(k in w["name"].lower() for k in LEFTOVER) and w not in empty]
    off = [w for w in workflows if not w["enabled"]]
    dormant_safe = [w for w in off if reach[w["id"]] == 0 and w not in empty]
    dormant_linked = [w for w in off if reach[w["id"]] > 0]
    live_stale = [w for w in workflows
                  if w["enabled"] and (d := _age_days(w["updated_at"], now)) is not None and d >= 365]

    contended = sorted(
        (p for p in analysis["properties"] if len(p["written_by_workflows"]) > 1),
        key=lambda p: -(len(p["read_by_workflows"]) + len(p["segmented_by_lists"])),
    )
    unused = sorted(
        (p for p in analysis["properties"] if p["unused"]),
        key=lambda p: (p["object_type"], p["name"]),
    )

    wf_name = {w["id"]: w["name"] for w in workflows}
    return {
        "p1": [row(w, reason="Empty — no steps") for w in empty]
              + [row(w, reason="Name suggests a leftover") for w in leftover],
        "p2": [row(w, reason="Turned off, nothing downstream")
               for w in sorted(dormant_safe, key=lambda w: w["name"].lower())],
        "p3": [row(w, reason=f"Turned off, {reach[w['id']]} downstream")
               for w in sorted(dormant_linked, key=lambda w: -reach[w["id"]])],
        "p4": [row(w, reason=f"Active, last edited {str(w['updated_at'] or '')[:10]}")
               for w in sorted(live_stale, key=lambda w: -reach[w["id"]])],
        "p5": [{
            "name": p.get("display") or p.get("label") or p["key"],
            "label": p["key"],
            "writers": [wf_name.get(i, i) for i in p["written_by_workflows"]],
            "writer_count": len(p["written_by_workflows"]),
            "readers": len(p["read_by_workflows"]) + len(p["segmented_by_lists"]),
            "link": p["link"],
        } for p in contended],
        "p6": [{
            "name": p.get("display") or p.get("label") or p["key"],
            "label": p["key"],
            "object": p["object_type"],
            "type": p.get("field_type") or p.get("type") or "",
            "group": p.get("group") or "",
            "link": p["link"],
            **_usage_fields(measured.get(p["key"])),
        } for p in sorted(unused, key=lambda p: (
            (measured.get(p["key"]) or {}).get("last_written") or "",
            (measured.get(p["key"]) or {}).get("fill_pct") or 0,
        ), reverse=True)],
    }


def _usage_fields(measured: dict[str, Any] | None) -> dict[str, Any]:
    """Fill rate and last-written, shaped for a spreadsheet row, with a verdict.

    Recency and source outrank fill rate, deliberately. A form field is only ever
    filled on the fraction of records that submitted that form, so judging it on
    fill rate alone marks live fields as empty — which is the exact mistake this
    measurement exists to prevent. A field written last month is in use at 0.1%
    fill; a field at 40% fill written last in 2021 is a fossil.

    Absent measurements read as "not measured" rather than as zero: an unmeasured
    field and an empty one must never look the same in a column someone acts on.
    """
    if not measured:
        return {"fill_pct": None, "filled": None, "last_written": "",
                "last_written_by": "", "written_by": [], "verdict": "Not measured"}

    pct = measured.get("fill_pct")
    last = measured.get("last_written") or ""
    source = measured.get("last_written_by") or ""
    fresh = bool(last and last >= _twelve_months_ago())

    if fresh:
        verdict = f"In use — {source.lower()} wrote it recently" if source else "In use — written recently"
    elif last:
        verdict = f"Last written {last[:7]} by {source.lower()}" if source else f"Last written {last[:7]}"
    elif pct == 0:
        verdict = "Safe to archive — no record holds a value"
    elif pct is not None and pct < 0.5:
        verdict = "Nearly empty, no write seen"
    elif pct is None:
        verdict = "No records on this object"
    else:
        verdict = "Filled, but no recent write seen"

    return {
        "fill_pct": pct, "filled": measured.get("filled"), "last_written": last,
        "last_written_by": source, "written_by": measured.get("written_by") or [],
        "verdict": verdict,
    }


def _twelve_months_ago() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year - 1:04d}-{now.month:02d}-{now.day:02d}"


def phases(analysis: dict[str, Any], work: dict[str, list]) -> list[dict[str, Any]]:
    """Phase metadata, with counts taken from the work lists so the two agree."""
    lists_ = analysis["lists"]
    emails = analysis["marketing_emails"]
    custom = [p for p in analysis["properties"] if not p["hubspot_defined"]]
    unreadable_lists = sum(1 for l in lists_ if not l.get("properties"))

    return [
        {
            "id": "p0", "n": 0, "title": "Protect the account", "risk": NONE,
            "count": "", "effort": "~30 min", "tab": None,
            "what": "Nothing is broken yet. This phase is the safety net that makes every later phase reversible.",
            "fix": "Take a full export and agree the rules of engagement. Ten minutes here is what lets you undo a mistake in week three.",
            "why": "HubSpot has no recycle bin for workflows. A deleted workflow is gone, and "
                   "its logic with it. Everything in this plan assumes you can undo a mistake; "
                   "this phase is what makes that true.",
            "where": "The audit already writes data/snapshot.json — it holds every workflow "
                     "definition in full. Keep it somewhere versioned.",
            "steps": [
                f"Export all {len(analysis['workflows'])} workflow definitions and commit them "
                "somewhere versioned.",
                "Agree who may edit workflows while the review runs. Two people editing during "
                "a cleanup produces changes nobody can attribute later.",
                "Write down the snapshot date. Every number here is as of that date, and the "
                "account keeps moving.",
                "Decide the disposal convention up front: turn off and rename with a prefix "
                "now, delete after an agreed waiting period. Renaming leaves a trail.",
            ],
            "guard": "Do not delete anything in later phases until the export exists and you "
                     "have confirmed it holds real definitions, not empty stubs.",
        },
        {
            "id": "p1", "n": 1, "title": "Clear the noise", "risk": SAFE,
            "count": f"{len(work['p1'])} workflows", "effort": "~2 hrs", "tab": "P1 Clear the noise",
            "what": "Workflows that contain nothing. Some were created and never built; others are copies someone made while testing and left behind. Neither does anything to your data.",
            "fix": "Delete the empty ones outright — there is no logic inside to lose. Open the copies and test-named ones first to be sure the name is telling the truth.",
            "why": "Workflows that carry no logic at all, plus those named as tests or copies. "
                   "Removing the empty ones is not a judgment call — there is nothing inside "
                   "them to lose.",
            "where": "Workbook → P1 tab, or the Workflows tab filtered to Steps = 0.",
            "steps": [
                "Delete the empty ones. Their footprint is provably zero — they reference "
                "nothing, so nothing can reference them.",
                "Open each leftover-named one individually. A name is a hint, not proof.",
                "Anything that turns out to have real steps belongs in Phase 3 or 4 instead — "
                "leave it and rename it properly.",
            ],
            "guard": "Do not bulk-delete on the name filter alone. “Copy of Lead Routing” may "
                     "be the version that is actually running.",
        },
        {
            "id": "p2", "n": 2, "title": "The provably dormant", "risk": SAFE,
            "count": f"{len(work['p2'])} workflows", "effort": "~half a day",
            "tab": "P2 Dormant safe",
            "what": "Workflows that are switched off AND whose output nothing else uses. Both halves matter: off on its own is not enough, because a dormant workflow can still hold the only definition of a field something live depends on.",
            "fix": "Rename with a prefix so they sort together, leave them a week, then delete. Note what each one did in the Notes column before it goes — that record is the only thing that survives deletion.",
            "why": f"{len(work['p2'])} turned-off workflows have nothing downstream at all — no "
                   "other workflow reads what they write, no list segments on it, no email "
                   "depends on it. That is measured from the dependency graph, not guessed, and "
                   "it is the strongest evidence you will get that removal is safe.",
            "where": "Workbook → P2 tab. Cross-check in the guide: the footprint line reads "
                     "“Nothing else depends on this”.",
            "steps": [
                "Work in batches of about twenty so any surprise is easy to trace.",
                "Re-confirm nothing downstream before each batch — the graph reflects the "
                "snapshot, and someone may have wired something up since.",
                "Apply the Phase 0 disposal convention rather than deleting outright.",
            ],
            "guard": "Turned off is not the same as never used. Contact records still show "
                     "historical enrolment. Note what each one did before it goes.",
        },
        {
            "id": "p3", "n": 3, "title": "Dormant clusters", "risk": JUDGE,
            "count": f"{len(work['p3'])} workflows", "effort": "~2 days",
            "tab": "P3 Dormant clusters",
            "what": "Workflows that are switched off but whose output something else still reads. Usually a retired system that was turned off as a group and still points at itself.",
            "fix": "Decide per cluster, not per workflow. If everything downstream is also dormant, retire the whole group. If anything downstream is live, find what feeds it now before touching anything.",
            "why": "These turned-off workflows do have something downstream. That usually means "
                   "a group of related workflows was retired together and still points at "
                   "itself. The question is whether the whole cluster is dormant or whether one "
                   "live thread runs through it.",
            "where": "Workbook → P3 tab, sorted by footprint. Open each in the guide and read "
                     "what it directly affects.",
            "steps": [
                "Every downstream item also off or unused → the cluster is dormant. Retire it "
                "as a unit, not one workflow at a time.",
                "Any downstream item is live → stop. Find out what writes that property now.",
                "If an active workflow already writes it, this one is redundant and can go. If "
                "nothing else does, the property is orphaned and you have found a real gap.",
                "Record the decision per cluster. This is the phase people redo six months "
                "later because nobody wrote down why.",
            ],
            "guard": "Do not delete one workflow out of a dormant cluster. Half a retired "
                     "system is harder to understand than all of it, and much harder to restore.",
        },
        {
            "id": "p4", "n": 4, "title": "Running but unreviewed", "risk": CARE,
            "count": f"{len(work['p4'])} workflows", "effort": "~1 week",
            "tab": "P4 Active and stale",
            "what": "Workflows that are running right now, and that nobody has opened in over a year. They are changing your records today using rules written for how the business used to work.",
            "fix": "You cannot fix these by reading the audit — this phase needs a conversation with whoever owns the process. Take the top twenty by footprint into one meeting and ask, for each: is this still how we do it? Change or switch off what no longer matches.",
            "why": f"{len(work['p4'])} workflows are active and have not been edited in over a "
                   "year. They are touching records today against logic nobody has checked "
                   "against how the business currently works. Everything before this was about "
                   "removing clutter. This is about correctness.",
            "where": "Workbook → P4 tab, already sorted by footprint — largest blast radius first.",
            "steps": [
                "Rank by footprint, not by age. The largest reach over a thousand assets each, "
                "so a wrong assumption there propagates furthest.",
                "For each of the top twenty, answer one question with the business owner: does "
                "this still describe how we work? Not “does it run” — it plainly does.",
                "Pay closest attention to anything writing lifecycle stage, deal stage or "
                "owner. Those drive reporting and routing, so an outdated rule distorts both.",
                "Timebox the rest. Sampling twenty at random tells you whether the problem is "
                "systemic or confined to the big ones.",
            ],
            "guard": "Do not treat “no changes needed” as the default outcome. This is the only "
                     "phase where leaving something alone is itself a decision with "
                     "consequences — it keeps acting on stale assumptions every day.",
        },
        {
            "id": "p5", "n": 5, "title": "Competing writes", "risk": JUDGE,
            "count": f"{len(work['p5'])} properties", "effort": "~2 days",
            "tab": "P5 Competing writes",
            "what": "Fields that more than one workflow sets. When two workflows can fire on the same record, whichever finishes last wins — which is why a value seems to change on its own.",
            "fix": "For each field, decide which workflow should win. Then either narrow the enrolment conditions so only one can fire, or merge the two into a single workflow with a branch. Write the intended order into the workflow description so nobody undoes it later.",
            "why": "These properties are written by more than one workflow — the usual cause of "
                   "a value that flips back and forth, a report that disagrees with the record, "
                   "and “this contact keeps changing owner”. Multiple writers are not "
                   "automatically wrong, but each one should be deliberate.",
            "where": "Workbook → P5 tab, sorted by how many things read the property.",
            "steps": [
                "Start with the properties the most other things read. A contested value that "
                "nothing consumes matters far less than one driving routing.",
                "For each, list the writers and establish the intended precedence: which should "
                "win, and under what condition.",
                "Where two writers can fire on the same record at once, add an enrolment "
                "condition so only one can, or merge them into a single branched workflow.",
                "Where the sequencing is intentional, write it into the workflow description so "
                "the next reviewer does not undo it.",
            ],
            "guard": "Do not assume a conflict. Two workflows writing the same property in a "
                     "deliberate order is valid design — the defect is nobody knowing the order.",
        },
        {
            "id": "p6", "n": 6, "title": "Unused fields", "risk": JUDGE,
            "count": f"{len(work['p6'])} of {len(custom)} custom", "effort": "~2 days",
            "tab": "P6 Unused fields",
            "what": "Custom fields that no workflow, form or list touches. They may still be filled in by hand, feed a report, or be written by an integration — none of which this audit can see.",
            "fix": "Check fill rate, reports and integrations first. Then archive rather than delete: archiving hides the field but keeps the historical values, and it is reversible.",
            "why": "These custom properties are referenced by no workflow, no form and no list. "
                   "That is a strong signal and it is not permission to delete. The audit can "
                   "only see automation — it cannot see a field a salesperson fills in on every "
                   "record, one feeding a report, or one an integration writes.",
            "where": "Workbook → P6 tab, sorted by fill rate, highest first.",
            "steps": [
                "Split by object. Contact and deal fields are far likelier to be filled by hand.",
                "For each candidate check the three things this audit cannot see: fill rate on "
                "real records, whether it appears in any report or dashboard, and whether an "
                "integration writes it — Salesforce sync fields especially.",
                "Anything with a meaningful fill rate stays, regardless of automation usage. It "
                "is being used, just not by a workflow.",
                "Archive what survives. Archiving preserves historical values; deleting does not.",
            ],
            "guard": "Do not bulk-delete on this number. It is the most dangerous figure in the "
                     "audit precisely because it looks so actionable. Archive first, delete only "
                     "after a quarter with no complaints.",
        },
        {
            "id": "p7", "n": 7, "title": "Marketing sprawl", "risk": JUDGE,
            "count": f"{len(lists_):,} lists · {len(emails):,} emails", "effort": "ongoing",
            "tab": None,
            "what": "The marketing library: every list, email and page. Individually low-risk, collectively the reason nobody can find anything.",
            "fix": "Work in batches by age and state rather than one at a time, and set a retention rule so this does not rebuild itself over the next year.",
            "why": "Marketing holds two thirds of the account. Per item the risk is low; in "
                   "aggregate it is the biggest drag on anyone trying to find anything. Treat "
                   "it as batch housekeeping rather than case-by-case review.",
            "where": "Workbook → Lists and Marketing emails tabs, sorted by last updated.",
            "steps": [
                f"{unreadable_lists:,} lists segment on no readable property — mostly static "
                "imports. Group by age; anything old with no workflow attached is a candidate.",
                "For emails, work by state first. Drafts never sent and campaigns long finished "
                "are the easy bulk.",
                "Before removing any list, check the guide for whether a workflow enrols from "
                "it. A list feeding live automation is not housekeeping.",
                "Set a retention rule going forward rather than doing this by hand again.",
            ],
            "guard": "Do not delete a list any active workflow enrols from or suppresses with, "
                     "however old it looks. Suppression lists are easy to mistake for abandoned.",
        },
        {
            "id": "p8", "n": 8, "title": "Hand it over", "risk": NONE,
            "count": "", "effort": "~half a day", "tab": None,
            "what": "Turning the work into something the next person can use without repeating it.",
            "fix": "Re-run the audit to show what changed, hand over the guide and workbook together, and teach one person the footprint check before they edit anything.",
            "why": "The point of the audit is not the cleanup — it is that the next person can "
                   "answer “what breaks if I change this” without rediscovering the account.",
            "where": "The guide and the workbook, handed over together.",
            "steps": [
                "Re-run the audit. Comparing new health scores against this snapshot is the "
                "clearest evidence of what the work achieved.",
                "Hand over the guide and the workbook together. The guide answers what is "
                "connected to what; the workbook is what people paste into a sheet.",
                "Show one person how to use the footprint check before editing a workflow. That "
                "single habit prevents most of what this audit found.",
                "Agree a cadence. Quarterly keeps the numbers from drifting back; annually is "
                "what produced this many unreviewed active workflows.",
            ],
            "guard": "",
        },
    ]
