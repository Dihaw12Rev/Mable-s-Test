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


def _plural(n: int, singular: str, plural: str | None = None) -> str:
    return f"{n} {singular if n == 1 else (plural or singular + 's')}"


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
    contended = [p for p in props if len(p["written_by_workflows"]) > 1]
    if contended:
        top = sorted(contended, key=lambda p: -len(p["written_by_workflows"]))[:3]
        out.append((
            f"{len(contended)} properties are written by more than one workflow",
            "Competing writes are the usual cause of values that flip back and forth. Worst: "
            + ", ".join(
                f"{p['key']} ({_plural(len(p['written_by_workflows']), 'workflow')})" for p in top
            )
            + ".",
        ))

    empty = [w for w in workflows if not w["action_count"]
             and not w["properties_written"] and not w["properties_read"]]
    if empty:
        out.append((
            f"{_plural(len(empty), 'workflow')} contain no steps at all",
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
            f"{_plural(len(test_like), 'workflow')} look like leftovers",
            "Named as tests, copies, or drafts: "
            + ", ".join(f"“{w['name']}”" for w in test_like[:4]) + ".",
        ))

    stale = [
        w for w in workflows
        if (d := _age_days(w["updated_at"], now)) is not None and d >= 365 and w["enabled"]
    ]
    if stale:
        out.append((
            f"{_plural(len(stale), 'active workflow')} have not been edited in over a year",
            "Still enrolling records against logic nobody has reviewed recently.",
        ))

    no_def = [w for w in workflows if not w["definition_available"]]
    if no_def:
        out.append((
            f"{_plural(len(no_def), 'workflow')} could not be read in full",
            "The token or plan tier did not expose their definitions, so their property "
            "dependencies are missing from this analysis.",
        ))

    orphan_forms = [f for f in a["forms"] if not f["archived"] and f["field_count"] == 0]
    if orphan_forms:
        out.append((
            f"{_plural(len(orphan_forms), 'live form')} collect no mapped fields",
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
    """The printed overview — the guide's landing page, minus the drilling-in.

    Deliberately the same five scores, the same findings and the same eight areas
    the interactive guide opens with, so a reader who has seen one recognises the
    other. Anything that only makes sense when clicked is left to the guide.
    """
    from . import areas as areas_mod
    from . import graph as graph_mod

    g = graph_mod.build(a)
    scores = areas_mod.health(a)
    portal_areas = areas_mod.build(a, g)
    obs = findings(a)

    counts: dict[str, int] = {}
    for node in g.nodes.values():
        counts[node["type"]] = counts.get(node["type"], 0) + 1
    order = ["workflow", "property", "list", "form", "email", "page", "pipeline", "stage"]

    generated = str(a.get("extracted_at") or "")[:10]
    body = [
        '<div class="page">',
        '<header class="mast">',
        '<div class="eyebrow">HubSpot account guide</div>',
        f"<h1>{escape(portal_name)}</h1>",
        '<div class="meta">'
        + (f'Portal {escape(str(a["portal_id"]))} · ' if portal_name != f"Portal {a['portal_id']}" else "")
        + f"snapshot {escape(generated)}</div>",
        "</header>",
        '<p class="lede">A plain-language map of everything running in this HubSpot account — '
        "what each piece does and what it is connected to. This is the summary; the '"
        "interactive guide lets you click into any area or asset.</p>",
    ]

    # -- health -----------------------------------------------------------
    body.append('<section class="block"><h2>Health check</h2>')
    body.append(
        '<p class="note">Five measures of how maintainable this account is today. Each says '
        "what it counted and why it matters.</p>"
    )
    body.append('<div class="dials">')
    for score in scores:
        body.append(
            '<div class="dial">'
            + charts.gauge(score["pct"], score["grade"])
            + f'<div class="dial-t">{escape(score["label"])}</div>'
            + f'<div class="dial-d">{escape(score["detail"])}</div>'
            + f'<div class="dial-w">{escape(score["why"])}</div>'
            "</div>"
        )
    body.append("</div></section>")

    # -- inventory + findings ---------------------------------------------
    rows = "".join(
        f"<tr><td>{escape(charts_label(t))}</td><td class='num'>{counts[t]}</td></tr>"
        for t in order if counts.get(t)
    )
    body += [
        '<section class="block"><h2>What is in the account</h2>',
        f'<table class="inv">{rows}</table>',
        "</section>",
    ]

    if obs:
        items = "".join(
            f'<li><span class="fh">{escape(h)}</span><span class="fd">{escape(d)}</span></li>'
            for h, d in obs
        )
        body += [
            '<section class="block"><h2>What we found</h2>',
            '<p class="note">The things most worth acting on, biggest first.</p>',
            f'<ul class="findings">{items}</ul>',
            "</section>",
        ]

    # -- areas -------------------------------------------------------------
    body += [
        '<section class="block"><h2>The account by area</h2>',
        '<p class="note">Each area groups the workflows, fields and assets that do one job '
        "together. In the interactive guide these are the doors you open.</p>",
        '<div class="areas">',
    ]
    for area in portal_areas:
        tags = "".join(
            f'<span class="tag"><b>{n}</b> {escape(_type_word(kind, n))}</span>'
            for kind, n in area["counts"].items()
        )
        body.append(
            '<div class="areacard">'
            f'<h3>{escape(area["name"])}</h3>'
            f'<p>{escape(area["blurb"])}</p>'
            f'<div class="tags">{tags}</div>'
            f'<div class="headline">{escape(area["headline"])}</div>'
            "</div>"
        )
    body.append("</div></section>")

    skipped = a.get("skipped") or []
    caveat = (
        "Connections are read from the account's own settings. Anything driven by an outside "
        "integration or custom code is not visible here, so treat every footprint as a minimum. "
        "HubSpot's API returns what a workflow does but not how many records it has touched, so "
        "nothing here is called unused on that basis — only turned off."
    )
    if skipped:
        caveat += " Not reachable with the token used: " + ", ".join(
            sorted({s["endpoint"] for s in skipped})
        ) + "."
    body += [
        '<section class="block caveat"><h2>How to read this</h2>',
        f'<p class="note">{escape(caveat)}</p>',
        '<p class="note">Asset-by-asset detail lives in the Account Reference document, and the '
        "full connection list is in the accompanying spreadsheet.</p>",
        "</section>",
        "</div>",
    ]
    return "".join(body)


def charts_label(kind: str) -> str:
    from . import graph as graph_mod

    return graph_mod.TYPE_PLURALS.get(kind, kind)


def _type_word(kind: str, n: int) -> str:
    from . import graph as graph_mod

    return graph_mod.TYPE_LABELS.get(kind, kind) if n == 1 else graph_mod.TYPE_PLURALS.get(kind, kind)
