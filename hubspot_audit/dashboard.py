"""Build the printed portal dashboard: derived figures, findings, and page HTML."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html import escape
from typing import Any

from . import charts

AGE_BUCKETS = [
    ("< 30d", 30),
    ("1–3mo", 90),
    ("3–6mo", 180),
    ("6–12mo", 365),
    ("1–2yr", 730),
    ("2yr+", 10**6),
]
STALE_FROM = 3  # index into AGE_BUCKETS where "not touched in a while" begins


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


def _bucket(days: int) -> int:
    for i, (_, limit) in enumerate(AGE_BUCKETS):
        if days < limit:
            return i
    return len(AGE_BUCKETS) - 1


# --------------------------------------------------------------------- findings


def findings(a: dict[str, Any]) -> list[tuple[str, str]]:
    """Derived observations, most consequential first. Each is (headline, detail)."""
    out: list[tuple[str, str]] = []
    now = datetime.now(timezone.utc)
    workflows = a["workflows"]
    props = a["properties"]
    custom = [p for p in props if not p["hubspot_defined"]]
    unused = [p for p in custom if p["unused"]]

    if not a.get("usage_complete", True):
        missing = [k for k, ok in (a.get("coverage") or {}).items() if not ok]
        out.append((
            "Property usage could not be measured",
            "This portal's " + " and ".join(missing) + " could not be read with the token "
            "supplied, so nothing here can say which properties are unreferenced. Every "
            "property below is reported as usage-unknown rather than unused. Re-run with the "
            "missing scopes granted before acting on any property.",
        ))

    if custom and unused:
        pct = round(len(unused) / len(custom) * 100)
        out.append((
            f"{len(unused)} of {len(custom)} custom properties ({pct}%) are referenced by nothing",
            "No workflow reads or writes them, no form collects them, no list segments on them. "
            "They are the first candidates for archiving.",
        ))

    off = [w for w in workflows if not w["enabled"]]
    if off:
        out.append((
            f"{len(off)} of {len(workflows)} workflows are turned off",
            "Turned-off workflows still hold logic and property dependencies. "
            + ", ".join(f"“{w['name']}”" for w in off[:4])
            + (f", and {len(off) - 4} more." if len(off) > 4 else "."),
        ))

    # Properties written by more than one active workflow are a contention risk.
    contended = [
        p for p in props
        if len([w for w in p["written_by_workflows"]]) > 1
    ]
    if contended:
        top = sorted(contended, key=lambda p: -len(p["written_by_workflows"]))[:3]
        out.append((
            f"{len(contended)} properties are written by more than one workflow",
            "Competing writes are the usual cause of values that flip back and forth. Worst: "
            + ", ".join(f"{p['name']} ({len(p['written_by_workflows'])} workflows)" for p in top)
            + ".",
        ))

    empty = [w for w in workflows if not w["action_count"]
             and not w["properties_written"] and not w["properties_read"]]
    if empty:
        out.append((
            f"{len(empty)} workflow(s) contain no steps at all",
            "No actions, no enrolment criteria, no property references — empty shells taking up "
            "space in the workflows list.",
        ))

    unnamed = [w for w in workflows if w["name"].lower().startswith("unnamed workflow")]
    if unnamed:
        pct = round(len(unnamed) / len(workflows) * 100)
        out.append((
            f"{len(unnamed)} of {len(workflows)} workflows ({pct}%) were never named",
            "They carry HubSpot's auto-generated “Unnamed workflow” title plus a timestamp, so "
            "nothing in the UI says what they are for. Their purpose here is inferred from "
            "behaviour instead.",
        ))

    test_like = [
        w for w in workflows
        if any(k in w["name"].lower() for k in ("test", "temp", "copy of", "draft", "[old", "delete"))
    ]
    if test_like:
        out.append((
            f"{len(test_like)} workflow(s) look like leftovers",
            "Named as tests, copies, or drafts: "
            + ", ".join(f"“{w['name']}”" for w in test_like[:4]) + ".",
        ))

    stale = [
        w for w in workflows
        if (d := _age_days(w["updated_at"], now)) is not None and d >= 365 and w["enabled"]
    ]
    if stale:
        out.append((
            f"{len(stale)} active workflow(s) have not been edited in over a year",
            "Still enrolling records against logic nobody has reviewed recently.",
        ))

    no_def = [w for w in workflows if not w["definition_available"]]
    if no_def:
        out.append((
            f"{len(no_def)} workflow(s) could not be read in full",
            "The token or plan tier did not expose their definitions, so their property "
            "dependencies are missing from this analysis.",
        ))

    orphan_forms = [f for f in a["forms"] if not f["archived"] and f["field_count"] == 0]
    if orphan_forms:
        out.append((
            f"{len(orphan_forms)} live form(s) collect no mapped fields",
            "Submissions land with nothing written to the CRM record.",
        ))

    return out


# ----------------------------------------------------------------- chart inputs


def system_rows(a: dict[str, Any]) -> list[tuple[str, list[int]]]:
    by_id = {w["id"]: w for w in a["workflows"]}
    rows = []
    for system, ids in a["systems"].items():
        members = [by_id[i] for i in ids if i in by_id]
        active = sum(1 for w in members if w["enabled"])
        rows.append((system, [active, len(members) - active]))
    return sorted(rows, key=lambda r: -sum(r[1]))


def top_property_rows(a: dict[str, Any], limit: int = 12) -> list[tuple[str, list[int]]]:
    # A name like `lifecyclestage` exists on several object types; unqualified it
    # would appear as duplicate rows. Qualify only the names that actually collide.
    seen: Counter[str] = Counter(p["name"] for p in a["properties"])
    rows = []
    for p in a["properties"][:limit]:
        wf = len(p["written_by_workflows"]) + len(p["read_by_workflows"])
        label = f"{p['object_type']}.{p['name']}" if seen[p["name"]] > 1 else p["name"]
        rows.append((label, [wf, len(p["collected_by_forms"]), len(p["segmented_by_lists"])]))
    return [r for r in rows if sum(r[1]) > 0]


def _present(rows: list[tuple[str, list[int]]], labels: list[tuple[str, str]]):
    """Drop legend entries whose series is empty across every row."""
    totals = [sum(values[i] for _, values in rows) for i in range(len(labels))]
    return [entry for entry, total in zip(labels, totals) if total > 0]


def inventory_rows(a: dict[str, Any]) -> list[tuple[str, list[int]]]:
    by_object: dict[str, list[int]] = {}
    for p in a["properties"]:
        slot = by_object.setdefault(p["object_type"], [0, 0, 0])
        if p["hubspot_defined"]:
            slot[0] += 1
        elif p["usage_score"] > 0:
            slot[1] += 1
        else:
            # Zero score: genuinely unreferenced when coverage is complete,
            # otherwise simply unmeasured. Same bucket, different label.
            slot[2] += 1
    return sorted(by_object.items(), key=lambda kv: -sum(kv[1]))


def recency_buckets(a: dict[str, Any]) -> list[tuple[str, int]]:
    now = datetime.now(timezone.utc)
    counts = Counter()
    for w in a["workflows"]:
        days = _age_days(w["updated_at"], now)
        if days is not None:
            counts[_bucket(days)] += 1
    return [(label, counts.get(i, 0)) for i, (label, _) in enumerate(AGE_BUCKETS)]


# ------------------------------------------------------------------------ page


def build_html(a: dict[str, Any], portal_name: str) -> str:
    workflows = a["workflows"]
    props = a["properties"]
    custom = [p for p in props if not p["hubspot_defined"]]
    unused = [p for p in custom if p["unused"]]
    active = sum(1 for w in workflows if w["enabled"])

    tiles = [
        ("Workflows", len(workflows), f"{active} active"),
        ("Properties", len(props), f"{len(custom)} custom"),
        ("Lists", len(a["lists"]), ""),
        ("Forms", len(a["forms"]), ""),
        ("Marketing emails", len(a["marketing_emails"]), ""),
        ("Landing pages", len(a["landing_pages"]), ""),
        ("Site pages", len(a["site_pages"]), ""),
        ("Owners", len(a["owners"]), ""),
    ]

    def tile(label, value, sub):
        return (
            f'<div class="tile"><div class="tv">{value}</div>'
            f'<div class="tk">{escape(label)}</div>'
            + (f'<div class="ts">{escape(sub)}</div>' if sub else "")
            + "</div>"
        )

    page_one_has_charts = False
    sys_rows = system_rows(a)
    prop_rows = top_property_rows(a)
    inv_rows = inventory_rows(a)
    buckets = recency_buckets(a)
    obs = findings(a)

    generated = str(a.get("extracted_at") or "")[:10]

    body = [
        '<div class="page">',
        '<header class="mast">',
        '<div class="eyebrow">HubSpot portal audit</div>',
        f"<h1>{escape(portal_name)}</h1>",
        # The heading already carries the portal number when the account has no name.
        f'<div class="meta">'
        + (f'Portal {escape(str(a["portal_id"]))} · ' if portal_name != f"Portal {a['portal_id']}" else "")
        + f"snapshot {escape(generated)} · {len(workflows)} workflows, "
        f"{len(props)} properties</div>",
        "</header>",
        '<div class="tiles">' + "".join(tile(*t) for t in tiles) + "</div>",
    ]

    if sys_rows:
        body += [
            '<section class="block">',
            "<h2>What this portal automates</h2>",
            '<p class="note">Workflows grouped by the job they do, inferred from their names and '
            "the properties they write.</p>",
            charts.legend(_present(sys_rows, [(charts.ACTIVE, "Active"), (charts.IDLE, "Turned off")])),
            charts.stacked_bars(sys_rows, [charts.ACTIVE, charts.IDLE]),
            "</section>",
        ]
        page_one_has_charts = True

    if any(v for _, v in buckets):
        stale_total = sum(v for i, (_, v) in enumerate(buckets) if i >= STALE_FROM)
        body += [
            '<section class="block">',
            "<h2>When workflows were last edited</h2>",
            f'<p class="note">{stale_total} workflow(s) have gone six months or more without a '
            "change. Amber marks those buckets.</p>",
            charts.column_bars(buckets, highlight_from=STALE_FROM),
            "</section>",
        ]
        page_one_has_charts = True

    # Only break when the opening page actually carried charts; otherwise a portal
    # with no readable workflows would print a page of white space.
    body.append('</div><div class="page">' if page_one_has_charts else "")

    if prop_rows:
        body += [
            '<section class="block">',
            "<h2>What the automation depends on</h2>",
            '<p class="note">The properties the portal leans on hardest, counted by how many '
            "workflows, forms, and lists reference each one.</p>",
            charts.legend(_present(prop_rows, [
                (charts.SERIES[0], "Workflows"),
                (charts.SERIES[1], "Forms"),
                (charts.SERIES[2], "Lists"),
            ])),
            charts.stacked_bars(prop_rows, charts.SERIES),
            "</section>",
        ]

    if inv_rows:
        complete = a.get("usage_complete", True)
        third_label = "Custom, unreferenced" if complete else "Custom, usage unknown"
        body += [
            '<section class="block">',
            "<h2>Property inventory</h2>",
            '<div class="split"><div class="split-main">',
            '<p class="note">Standard properties against custom ones, split by whether anything '
            "in the portal references them.</p>" if complete else
            '<p class="note">Standard properties against custom ones. Usage could not be measured '
            "for this portal, so no custom property is claimed to be unreferenced.</p>",
            charts.legend(_present(inv_rows, [
                (charts.IDLE, "HubSpot standard"),
                (charts.SERIES[0], "Custom, in use"),
                (charts.WARNING, third_label),
            ])),
            charts.stacked_bars(inv_rows, [charts.IDLE, charts.SERIES[0], charts.WARNING], width=470),
            "</div><div class='split-side'>",
        ]
        if complete:
            body += [
                charts.donut_share(len(unused), len(custom)),
                f'<div class="dial-k">of {len(custom)} custom properties<br>'
                "are referenced by nothing</div>",
            ]
        else:
            body += [
                '<div class="unknown-dial">?</div>',
                f'<div class="dial-k">usage of {len(custom)} custom<br>properties is unmeasured</div>',
            ]
        body.append("</div></div></section>")

    if obs:
        items = "".join(
            f'<li><span class="fh">{escape(h)}</span><span class="fd">{escape(d)}</span></li>'
            for h, d in obs
        )
        body += [
            '<section class="block">',
            "<h2>What stands out</h2>",
            f'<ul class="findings">{items}</ul>',
            "</section>",
        ]

    skipped = a.get("skipped") or []
    caveat = (
        "Workflow definitions come from HubSpot's v4 Automation API, which returns logic but not "
        "enrollment history — how many records a workflow has touched lives only in the HubSpot UI, "
        "so nothing here is called unused on that basis. Property references are resolved by exact "
        "name match against this portal's own schema, so a reference made through an integration or "
        "a custom-coded action will not appear."
    )
    if skipped:
        caveat += " Endpoints not reachable with the supplied token: " + ", ".join(
            sorted({s["endpoint"] for s in skipped})
        ) + "."
    body += [
        '<section class="block caveat">',
        "<h2>How to read this</h2>",
        f'<p class="note">{escape(caveat)}</p>',
        '<p class="note">Full asset-by-asset detail, including every workflow\'s step breakdown and '
        "the complete property table, is in the accompanying Portal Reference document.</p>",
        "</section>",
        "</div>",
    ]
    return "".join(body)
