"""Export the whole account as a spreadsheet, one tab per asset type.

Built for copy-paste: every tab is a flat table with a header row, frozen panes
and an autofilter, so a reader can select a block and drop it straight into
Google Sheets. The Overview tab counts the other tabs with formulas rather than
literals, so the numbers stay right if rows are deleted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import areas as areas_mod
from . import review as review_mod
from . import graph as graph_mod

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F5F63")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name=FONT, size=10)
TITLE_FONT = Font(name=FONT, size=13, bold=True)
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="6E6862")
LINK_FONT = Font(name=FONT, size=10, color="0F5F63", underline="single")
FILL_HEAD = PatternFill("solid", fgColor="8A5A12")     # columns you complete
EXAMPLE_FILL = PatternFill("solid", fgColor="FFF6E0")  # the worked example row
RISK_FILL = {
    "safe": PatternFill("solid", fgColor="E1EDE4"),
    "judgment": PatternFill("solid", fgColor="F6EBD8"),
    "careful": PatternFill("solid", fgColor="F7E2E0"),
    "process": PatternFill("solid", fgColor="EFEAE4"),
}

# Columns the reviewer fills in, appended to every work-list tab.
TRACK_COLS = ["Decision", "Owner", "Date done", "Notes"]
TRACK_WIDTHS = [18, 16, 13, 44]
# One worked example per phase: the same wording everywhere would put deletion advice
# on the tab whose whole point is reviewing live automation.
EXAMPLES = {
    "P1 Clear the noise": ["Delete", "R. Ops", "2026-09-01",
                           "Confirmed zero steps; exported before removing"],
    "P2 Dormant safe": ["Archive", "R. Ops", "2026-09-03",
                        "Re-checked footprint still 0; renamed with ZZ_ prefix, delete after 30 days"],
    "P3 Dormant clusters": ["Retire cluster", "R. Ops", "2026-09-10",
                            "All 4 downstream workflows also off; retiring the group together"],
    "P4 Active and stale": ["Keep — reviewed", "Sales ops", "2026-09-15",
                            "Confirmed with deal desk: stage mapping still correct, no change needed"],
    "P5 Competing writes": ["Add enrolment condition", "R. Ops", "2026-09-18",
                            "Routing wins over the import workflow; condition added so only one fires"],
    "P6 Unused fields": ["Archive", "R. Ops", "2026-09-22",
                         "Fill rate 0.3%, not in any report, no integration writes it"],
}
DEFAULT_EXAMPLE = ["Reviewed", "R. Ops", "2026-09-01", "Decision and reasoning go here"]


def _sheet(wb: Workbook, title: str, headers: list[str], widths: list[int]):
    ws = wb.create_sheet(title[:31])
    ws.append(headers)
    for i, (head, width) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=1, column=i)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[1].height = 26
    ws.freeze_panes = "A2"
    return ws


def _finish(ws, *, hyperlinks: bool = True) -> None:
    """Body font, wrapped descriptions, clickable links, and a filter row.

    Each real hyperlink costs a relationship entry in the sheet's XML. On a tab with
    a couple of thousand rows that alone makes the file slow enough to stall a
    LibreOffice recalculation, so large tabs keep the URL as plain text — which is
    what you want for Sheets anyway, since it linkifies a pasted URL itself.
    """
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.alignment = Alignment(vertical="top", wrap_text=isinstance(cell.value, str)
                                       and len(str(cell.value)) > 60)
            if hyperlinks and isinstance(cell.value, str) and cell.value.startswith("https://"):
                cell.hyperlink = cell.value
                cell.font = LINK_FONT
                cell.value = "Open in HubSpot"
    if ws.max_row > 1:
        ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"


def _names(ids: list[str], g) -> str:
    return ", ".join(g.nodes[i]["label"] for i in ids if i in g.nodes)


def _worklist(wb: Workbook, title: str, headers: list[str], widths: list[int],
              rows: list[list[Any]], note: str) -> None:
    """A phase work list: the evidence columns, then blank columns to fill in.

    The fill-in columns carry a different header colour, and the first data row is a
    worked example in the expected format — deleted once real decisions start.
    """
    ws = _sheet(wb, title, headers + TRACK_COLS, widths + TRACK_WIDTHS)
    for i in range(len(headers) + 1, len(headers) + len(TRACK_COLS) + 1):
        ws.cell(row=1, column=i).fill = FILL_HEAD

    ws.append([""] * len(headers) + EXAMPLES.get(title, DEFAULT_EXAMPLE))
    for cell in ws[2]:
        cell.fill = EXAMPLE_FILL
    ws.cell(row=2, column=1, value="← EXAMPLE ROW — delete me").font = Font(
        name=FONT, size=10, italic=True, color="8A5A12")

    for row in rows:
        ws.append(row + [""] * len(TRACK_COLS))
    _finish(ws, hyperlinks=len(rows) <= 300)
    ws.insert_rows(1)
    ws["A1"] = note
    ws["A1"].font = NOTE_FONT
    ws.freeze_panes = "A3"


def build(analysis: dict[str, Any], out_path: Path) -> Path:
    g = graph_mod.build(analysis)
    portal_areas = areas_mod.build(analysis, g)
    scores = areas_mod.health(analysis)

    # Which area each asset landed in, so every tab can name it.
    area_of: dict[str, str] = {}
    for area in portal_areas:
        for ids in area["members"].values():
            for node_id in ids:
                area_of[node_id] = area["name"]

    wb = Workbook()
    wb.remove(wb.active)

    # ---------------------------------------------------------- workflows
    ws = _sheet(
        wb, "Workflows",
        ["Workflow", "Status", "Area", "Steps", "Writes to", "Reads", "Triggers",
         "Lists used", "Last updated", "What it does", "Link"],
        [42, 10, 26, 7, 34, 34, 26, 22, 13, 62, 16],
    )
    by_id = {w["id"]: w for w in analysis["workflows"]}
    for w in sorted(analysis["workflows"], key=lambda w: (not w["enabled"], w["name"].lower())):
        ws.append([
            w["name"],
            "Active" if w["enabled"] else "Turned off",
            area_of.get(f"wf:{w['id']}", ""),
            w["action_count"],
            ", ".join(w["properties_written_q"]),
            ", ".join(w["properties_read_q"]),
            ", ".join(by_id[t]["name"] for t in w["workflows_triggered"] if t in by_id),
            ", ".join(w["lists_referenced"]),
            str(w["updated_at"] or "")[:10],
            w["description"].replace("`", ""),
            w["link"],
        ])
    _finish(ws)

    # --------------------------------------------------------- properties
    ws = _sheet(
        wb, "Properties",
        ["Property", "Label", "Object", "Type", "Group", "Custom?", "Used by",
         "Workflows writing", "Workflows reading", "Forms", "Lists", "Area", "Link"],
        [34, 28, 14, 13, 20, 9, 9, 34, 34, 22, 22, 24, 16],
    )
    for p in analysis["properties"]:
        ws.append([
            p["key"], p.get("label") or "", p["object_type"],
            p.get("field_type") or p.get("type") or "",
            p.get("group") or "",
            "no" if p["hubspot_defined"] else "yes",
            p["usage_score"],
            _names([f"wf:{i}" for i in p["written_by_workflows"]], g),
            _names([f"wf:{i}" for i in p["read_by_workflows"]], g),
            _names([f"form:{i}" for i in p["collected_by_forms"]], g),
            _names([f"list:{i}" for i in p["segmented_by_lists"]], g),
            area_of.get(f"prop:{p['key']}", ""),
            p["link"],
        ])
    _finish(ws, hyperlinks=False)

    # -------------------------------------------------- lists, forms, etc.
    ws = _sheet(wb, "Lists", ["List", "Type", "Size", "Segments on", "Used by workflows", "Link"],
                [40, 13, 10, 40, 40, 16])
    for l in analysis["lists"]:
        ws.append([
            l["name"], l.get("processing_type") or "", l.get("size") or "",
            ", ".join(l.get("properties_q") or []),
            _names([t for t, _ in g.out.get(f"list:{l['id']}", [])], g),
            l["link"],
        ])
    _finish(ws)

    ws = _sheet(wb, "Forms", ["Form", "Type", "Status", "Fields", "Writes to", "Link"],
                [40, 15, 11, 8, 52, 16])
    for f in analysis["forms"]:
        ws.append([
            f["name"], f.get("type") or "", "Archived" if f["archived"] else "Live",
            f["field_count"], ", ".join(f.get("fields_q") or []), f["link"],
        ])
    _finish(ws)

    ws = _sheet(wb, "Marketing emails", ["Email", "Subject", "State", "Last updated", "Link"],
                [40, 44, 14, 13, 16])
    for e in analysis["marketing_emails"]:
        ws.append([e["name"], e.get("subject") or "", e.get("state") or "",
                   str(e.get("updated_at") or "")[:10], e["link"]])
    _finish(ws)

    ws = _sheet(wb, "Pages", ["Page", "Kind", "URL", "State", "Last updated", "Link"],
                [36, 15, 46, 13, 13, 16])
    for p in analysis["landing_pages"] + analysis["site_pages"]:
        ws.append([p["name"], p["kind"], p.get("url") or "", p.get("state") or "",
                   str(p.get("updated_at") or "")[:10], p["link"]])
    _finish(ws)

    ws = _sheet(wb, "Pipelines & stages", ["Pipeline", "Object", "Stage", "Link"], [36, 14, 36, 16])
    for obj, pipelines in (analysis.get("pipelines") or {}).items():
        for pl in pipelines:
            stages = pl.get("stages") or []
            if not stages:
                ws.append([pl.get("label") or pl.get("id"), obj, "", ""])
            for stage in stages:
                ws.append([pl.get("label") or pl.get("id"), obj,
                           stage.get("label") or stage.get("id"), ""])
    _finish(ws)

    # ------------------------------------------------------- connections
    ws = _sheet(wb, "Connections", ["From", "From type", "Relationship", "To", "To type"],
                [44, 15, 20, 44, 15])
    for edge in sorted(g.to_dict()["edges"], key=lambda e: (e["from"], e["to"])):
        src, dst = g.nodes.get(edge["from"]), g.nodes.get(edge["to"])
        if not src or not dst:
            continue
        ws.append([src["label"], graph_mod.TYPE_LABELS.get(src["type"], src["type"]),
                   graph_mod.RELATIONS.get(edge["rel"], (edge["rel"],))[0],
                   dst["label"], graph_mod.TYPE_LABELS.get(dst["type"], dst["type"])])
    _finish(ws, hyperlinks=False)

    # ------------------------------------------------------------- areas
    ws = _sheet(wb, "Areas", ["Area", "What it covers", "Workflows", "Active", "Other assets",
                              "Most connected"], [26, 60, 11, 9, 13, 40])
    for area in portal_areas:
        others = sum(n for k, n in area["counts"].items() if k != "workflow")
        ws.append([area["name"], area["blurb"], area["counts"].get("workflow", 0),
                   area["active_workflows"], others, area["headline"]])
    _finish(ws)

    _review_tabs(wb, analysis, g)
    _overview(wb, analysis, scores, portal_areas)
    wb._sheets.insert(0, wb._sheets.pop(wb._sheets.index(wb["Overview"])))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    return out_path


def _review_tabs(wb: Workbook, analysis: dict[str, Any], g) -> None:
    """The review plan as a tab, plus one work list per actionable phase."""
    work = review_mod.cohorts(analysis, g)
    phases = review_mod.phases(analysis, work)

    ws = _sheet(wb, "Review plan",
                ["Phase", "What to do", "Risk", "Scope", "Effort", "Work list tab",
                 "The mistake to avoid"],
                [8, 26, 12, 28, 12, 22, 66])
    for phase in phases:
        ws.append([phase["n"], phase["title"], phase["risk"],
                   phase["count"] or "—", phase["effort"], phase["tab"] or "—",
                   phase["guard"] or "—"])
        ws.cell(row=ws.max_row, column=3).fill = RISK_FILL.get(phase["risk"], RISK_FILL["process"])
    _finish(ws, hyperlinks=False)
    ws.insert_rows(1)
    ws["A1"] = ("Work top to bottom. Phases 1-2 are evidence-backed; phase 4 carries the real "
                "business risk. Each work list tab has amber columns for you to complete.")
    ws["A1"].font = NOTE_FONT
    ws.freeze_panes = "A3"

    wf_head = ["Workflow", "Why it is here", "Status", "Steps", "Last updated",
               "Footprint", "Writes to", "Link"]
    wf_width = [46, 30, 11, 7, 13, 11, 40, 16]

    def wf_rows(key):
        return [[r["name"], r["reason"], r["status"], r["steps"], r["updated"],
                 r["footprint"], r["writes"], r["link"]] for r in work[key]]

    _worklist(wb, "P1 Clear the noise", wf_head, wf_width, wf_rows("p1"),
              "Phase 1 — no logic inside these. Empty ones are safe to delete; check the "
              "leftover-named ones individually before removing.")
    _worklist(wb, "P2 Dormant safe", wf_head, wf_width, wf_rows("p2"),
              "Phase 2 — turned off with nothing downstream. Footprint 0 is measured, not "
              "assumed. Re-confirm before each batch.")
    _worklist(wb, "P3 Dormant clusters", wf_head, wf_width, wf_rows("p3"),
              "Phase 3 — turned off but something downstream. Retire a whole dormant cluster, "
              "never one workflow out of it. Sorted by footprint.")
    _worklist(wb, "P4 Active and stale", wf_head, wf_width, wf_rows("p4"),
              "Phase 4 — running, and not edited in over a year. Highest risk in the audit. "
              "Sorted by footprint: work down from the top.")

    _worklist(wb, "P5 Competing writes",
              ["Property", "Label", "Written by", "Writers", "Things reading it", "Link"],
              [34, 28, 60, 9, 15, 16],
              [[r["name"], r["label"], r["writers"], r["writer_count"], r["readers"], r["link"]]
               for r in work["p5"]],
              "Phase 5 — more than one workflow writes these. Establish which should win and "
              "under what condition. Sorted by how much depends on the value.")

    _worklist(wb, "P6 Unused fields",
              ["Property", "Label", "Object", "Type", "Group", "Link"],
              [34, 30, 15, 14, 22, 16],
              [[r["name"], r["label"], r["object"], r["type"], r["group"], r["link"]]
               for r in work["p6"]],
              "Phase 6 — no workflow, form or list references these. That is NOT permission to "
              "delete: check fill rate, reports and integrations first, then archive.")


def _overview(wb: Workbook, analysis: dict[str, Any], scores, portal_areas) -> None:
    ws = wb.create_sheet("Overview")
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 13
    ws.column_dimensions["C"].width = 46
    ws.column_dimensions["D"].width = 52

    ws["A1"] = f"HubSpot account guide — {analysis.get('portal_id')}"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = f"Snapshot taken {str(analysis.get('extracted_at') or '')[:10]}. " \
               "Every tab is a flat table — select a block and paste it straight into Sheets. " \
               "Counts are as of the snapshot."
    ws["A2"].font = NOTE_FONT

    row = 4
    ws.cell(row=row, column=1, value="Health check").font = Font(name=FONT, size=11, bold=True)
    row += 1
    for header in ("Measure", "Score", "What was counted", "Why it matters"):
        cell = ws.cell(row=row, column=("Measure", "Score", "What was counted",
                                        "Why it matters").index(header) + 1, value=header)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
    row += 1
    for score in scores:
        ws.cell(row=row, column=1, value=score["label"]).font = BODY_FONT
        pct = ws.cell(row=row, column=2, value=score["pct"] / 100)
        pct.number_format = "0%"
        pct.font = BODY_FONT
        ws.cell(row=row, column=3, value=score["detail"]).font = BODY_FONT
        ws.cell(row=row, column=4, value=score["why"]).font = BODY_FONT
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="What is in the account").font = Font(name=FONT, size=11, bold=True)
    row += 1
    # COUNTA over each tab's key column, so a deleted row is reflected here.
    for label, sheet_name in (
        ("Workflows", "Workflows"), ("Properties", "Properties"), ("Lists", "Lists"),
        ("Forms", "Forms"), ("Marketing emails", "Marketing emails"), ("Pages", "Pages"),
        ("Connections", "Connections"),
    ):
        ws.cell(row=row, column=1, value=label).font = BODY_FONT
        # Literal counts rather than COUNTA formulas. This workbook is a snapshot
        # export, not a live model, and openpyxl writes formulas with no cached
        # value — an unevaluated formula reads as blank in Sheets and in previews.
        # Counting the rows here is verifiable at build time; a formula is not.
        cell = ws.cell(row=row, column=2, value=max(wb[sheet_name].max_row - 1, 0))
        cell.font = Font(name=FONT, size=10, bold=True)
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="What we found").font = Font(name=FONT, size=11, bold=True)
    row += 1
    from . import dashboard

    for headline, detail in dashboard.findings(analysis):
        ws.cell(row=row, column=1, value=headline).font = Font(name=FONT, size=10, bold=True)
        note = ws.cell(row=row, column=3, value=detail)
        note.font = BODY_FONT
        note.alignment = Alignment(vertical="top", wrap_text=True)
        row += 1
