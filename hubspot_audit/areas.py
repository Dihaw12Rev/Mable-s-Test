"""Group the portal into business areas a non-specialist already understands.

A flat list of a few thousand assets is unusable as a handover document. People
do not think "show me property 1,482"; they think "how does our sales pipeline
work". Each area below collects the assets that serve one job, so the reader
starts from a concept they recognise and drills down from there.

Also computes the plain-language health grades shown on the overview.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

# Which workflow systems belong to which area. A system maps to exactly one area
# so no workflow is counted twice.
SYSTEM_TO_AREA = {
    "Sales & Deal Automation": "pipelines",
    "Record Creation & Association": "pipelines",
    "Lifecycle & Stage Management": "lifecycle",
    "Lead Scoring & Qualification": "lifecycle",
    "Customer Onboarding & Success": "lifecycle",
    "Lead Routing & Assignment": "routing",
    "Internal Notifications & Tasks": "routing",
    "Support & Ticketing": "support",
    "Nurture & Marketing Campaigns": "marketing",
    "Deliverability & Suppression": "marketing",
    "Integrations & App Actions": "integrations",
    "Data Hygiene & Automation": "data",
    "Other Automation": "data",
    "Empty — no steps configured": "attention",
}

AREAS = [
    ("pipelines", "Sales Pipelines",
     "Your deal pipelines and the automation that moves deals between stages. "
     "Start here to see how a deal travels from first contact to closed."),
    ("lifecycle", "Lifecycle & Lead Management",
     "How a contact is graded and promoted — from a new lead through to a customer — "
     "and the properties that record where they are."),
    ("routing", "Ownership & Notifications",
     "Who owns a record, how it gets assigned, and which alerts and tasks fire for "
     "your team when something needs attention."),
    ("support", "Support & Ticketing",
     "Ticket handling: how tickets change status, who gets notified, and what "
     "happens when a customer replies."),
    ("marketing", "Marketing & Campaigns",
     "The forms people fill in, the emails they receive, the pages they land on, "
     "and the lists that decide who gets what."),
    ("integrations", "Integrations & Apps",
     "Places where HubSpot hands work to another tool — Slack, Jira, spreadsheets — "
     "or runs custom code."),
    ("data", "Data & Properties",
     "The fields your records store, which ones your automation actually relies on, "
     "and the housekeeping workflows that keep them tidy."),
    ("attention", "Needs Attention",
     "Workflows that are empty, unnamed, or long untouched. Nothing here is doing "
     "useful work as it stands."),
]


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


def _grade(pct: float) -> str:
    for cutoff, letter in ((90, "A"), (80, "B"), (65, "C"), (50, "D")):
        if pct >= cutoff:
            return letter
    return "F"


def health(a: dict[str, Any]) -> list[dict[str, Any]]:
    """Five plain-language scores. Each states what it measures and why it matters."""
    now = datetime.now(timezone.utc)
    workflows = a["workflows"]
    props = a["properties"]
    custom = [p for p in props if not p["hubspot_defined"]]
    total_wf = len(workflows) or 1

    named = sum(1 for w in workflows if not re.match(r"^\s*unnamed workflow", w["name"], re.I))
    with_steps = sum(1 for w in workflows if w["action_count"])
    fresh = sum(1 for w in workflows
                if (d := _age_days(w["updated_at"], now)) is not None and d < 365)
    used_custom = sum(1 for p in custom if p["usage_score"] > 0)
    connected_lists = sum(1 for l in a["lists"] if l.get("properties"))

    scores = [
        ("Documentation", named / total_wf * 100,
         f"{named} of {len(workflows)} workflows carry a real name",
         "An unnamed workflow is invisible to whoever inherits it."),
        ("Workflow hygiene", with_steps / total_wf * 100,
         f"{with_steps} of {len(workflows)} workflows actually do something",
         "Empty workflows clutter the list and hide the ones that matter."),
        ("Upkeep", fresh / total_wf * 100,
         f"{fresh} of {len(workflows)} were edited in the last year",
         "Automation nobody has reviewed drifts away from how the business works."),
        ("Property discipline", (used_custom / len(custom) * 100) if custom else 100,
         f"{used_custom} of {len(custom)} custom fields are actually used",
         "Unused fields make forms and reports harder to get right."),
        ("List hygiene", (connected_lists / len(a["lists"]) * 100) if a["lists"] else 100,
         f"{connected_lists} of {len(a['lists'])} lists segment on a known property",
         "A list with no readable criteria cannot be reasoned about."),
    ]
    return [
        {"label": label, "pct": round(pct), "grade": _grade(pct), "detail": detail, "why": why}
        for label, pct, detail, why in scores
    ]


def overall(scores: list[dict[str, Any]]) -> str:
    return _grade(sum(s["pct"] for s in scores) / len(scores)) if scores else "—"


def build(a: dict[str, Any], g) -> list[dict[str, Any]]:
    """Assign every asset to exactly one area and summarise each."""
    wf_area: dict[str, str] = {}
    for system, ids in a["systems"].items():
        area = SYSTEM_TO_AREA.get(system, "data")
        for wid in ids:
            wf_area[wid] = area

    buckets: dict[str, dict[str, list[str]]] = {
        key: {"workflow": [], "property": [], "list": [], "form": [],
              "email": [], "page": [], "pipeline": [], "stage": []}
        for key, _, _ in AREAS
    }

    for w in a["workflows"]:
        buckets[wf_area.get(w["id"], "data")]["workflow"].append(f"wf:{w['id']}")

    # Pipelines and their stages are the backbone of the sales area.
    for node_id, node in g.nodes.items():
        if node["type"] in ("pipeline", "stage"):
            buckets["pipelines"][node["type"]].append(node_id)

    # Marketing owns the assets a customer actually sees.
    for f in a["forms"]:
        buckets["marketing"]["form"].append(f"form:{f['id']}")
    for e in a["marketing_emails"]:
        buckets["marketing"]["email"].append(f"email:{e['id']}")
    for p in a["landing_pages"] + a["site_pages"]:
        buckets["marketing"]["page"].append(f"page:{p['id']}")
    for l in a["lists"]:
        buckets["marketing"]["list"].append(f"list:{l['id']}")

    # A property belongs to the area whose workflows lean on it hardest; anything
    # no workflow touches lives in Data & Properties.
    for p in a["properties"]:
        node_id = f"prop:{p['key']}"
        if node_id not in g.nodes:
            continue
        votes: dict[str, int] = {}
        for wid in p["written_by_workflows"] + p["read_by_workflows"]:
            area = wf_area.get(wid)
            if area and area != "attention":
                votes[area] = votes.get(area, 0) + 1
        home = max(votes, key=votes.get) if votes else "data"
        buckets[home]["property"].append(node_id)

    out = []
    for key, name, blurb in AREAS:
        members = buckets[key]
        total = sum(len(v) for v in members.values())
        if not total:
            continue
        active = sum(
            1 for nid in members["workflow"]
            if g.nodes.get(nid, {}).get("enabled")
        )
        out.append({
            "id": key,
            "name": name,
            "blurb": blurb,
            "members": {k: v for k, v in members.items() if v},
            "counts": {k: len(v) for k, v in members.items() if v},
            "total": total,
            "active_workflows": active,
            "headline": _headline(key, members, g, active),
        })
    return out


def _headline(key: str, members: dict[str, list[str]], g, active: int) -> str:
    """One sentence naming the most load-bearing thing in this area."""
    wf = members.get("workflow") or []
    if not wf:
        counts = ", ".join(f"{len(v)} {k}s" for k, v in members.items() if v)
        return f"{counts}."
    busiest = max(wf, key=lambda n: len(g.out.get(n, [])) + len(g.inc.get(n, [])))
    label = g.nodes[busiest]["label"]
    return f"{len(wf)} workflows ({active} running). Most connected: “{label}”."
