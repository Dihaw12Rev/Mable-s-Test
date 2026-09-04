"""A small workbook covering only the three follow-up requests.

The full inventory answers everything about the account; this one answers three
questions and nothing else, so it can be opened and read without hunting through
seventeen tabs. It is a reference, not a worklist — there are no columns to fill
in, because the decisions belong on the P6 tab of the main workbook.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import review as review_mod

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F5F63")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
BODY = Font(name=FONT, size=10)
TITLE = Font(name=FONT, size=13, bold=True)
SECTION = Font(name=FONT, size=11, bold=True)
NOTE = Font(name=FONT, size=9, italic=True, color="5F5952")
LINK = Font(name=FONT, size=10, color="0F5F63", underline="single")

# Verdict groups, coloured so the ones that must not be touched stand out.
VERDICT_FILL = {
    "keep": PatternFill("solid", fgColor="F7E2E0"),   # in use — leave alone
    "judge": PatternFill("solid", fgColor="F6EBD8"),  # dated write — judgement
    "safe": PatternFill("solid", fgColor="E1EDE4"),   # empty — archive
}

# What was tested for request 1, and what HubSpot returned. Recorded so the
# conclusion can be re-checked rather than taken on trust.
ENDPOINT_EVIDENCE = [
    ("GET", "/automation/v4/flows/{id}/performance", "404", "No such endpoint"),
    ("GET", "/automation/v3/workflows/{id}/performance", "404", "No such endpoint"),
    ("GET", "/automation/v2/workflows/{id}/performance", "404", "No such endpoint"),
    ("GET", "/automation/v2/workflows/{id}", "404", "No such endpoint"),
    ("GET", "/automation/v3/workflows/{id}", "404", "No such endpoint"),
    ("GET", "/automation/v4/flows/{id}/metrics", "404", "No such endpoint"),
    ("GET", "/automation/v4/flows/{id}/enrollments", "404", "No such endpoint"),
    ("GET", "/automation/v2/workflows/{id}/enrollments/contacts", "404", "No such endpoint"),
    ("GET", "/automation/v4/flows/{id}/actions", "404", "No such endpoint"),
    ("GET", "/crm/v3/properties/contacts/hs_all_active_workflow_ids", "404",
     "Property does not exist in this portal"),
    ("GET", "/crm/v3/properties/contacts/currentlyinworkflow", "200",
     "Exists, but HubSpot labels it “(discontinued)”"),
    ("GET", "record property history", "200",
     "Automation writes read as enrollmentId:…;actionExecutionIndex:N — the enrolment, "
     "never the workflow"),
]


def _sheet(wb: Workbook, title: str, headers: list[str], widths: list[int], note: str):
    ws = wb.create_sheet(title[:31])
    ws.append([note])
    ws["A1"].font = NOTE
    ws.append(headers)
    for i, (head, width) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=2, column=i)
        cell.fill, cell.font = HEAD_FILL, HEAD_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[2].height = 26
    ws.freeze_panes = "A3"
    return ws


def _finish(ws, percent_headers: set[str] = frozenset()) -> None:
    headers = {ws.cell(row=2, column=c).value: c for c in range(1, ws.max_column + 1)}
    for row in ws.iter_rows(min_row=3):
        for cell in row:
            cell.font = BODY
            text = cell.value if isinstance(cell.value, str) else ""
            cell.alignment = Alignment(vertical="top", wrap_text="\n" in text or len(text) > 55)
            if text.startswith("https://"):
                cell.value = f'=HYPERLINK("{text}","Open in HubSpot")'
                cell.font = LINK
    for head in percent_headers:
        col = headers.get(head)
        if col:
            for row in range(3, ws.max_row + 1):
                ws.cell(row=row, column=col).number_format = "0.0%"
    if ws.max_row > 2:
        ws.auto_filter.ref = f"A2:{get_column_letter(ws.max_column)}{ws.max_row}"


def _group(verdict: str) -> str:
    if verdict.startswith("In use"):
        return "keep"
    if verdict.startswith("Safe to archive") or verdict.startswith("Nearly empty"):
        return "safe"
    return "judge"


def build(analysis: dict[str, Any], out_path: Path) -> Path:
    from . import graph as graph_mod

    g = graph_mod.build(analysis)
    work = review_mod.cohorts(analysis, g)
    measured = (analysis.get("usage") or {}).get("properties") or {}
    usage_meta = analysis.get("usage") or {}

    wb = Workbook()
    wb.remove(wb.active)

    _readme(wb, analysis, work, measured, usage_meta)
    _request1(wb, work)
    _request23(wb, work)
    _all_fields(wb, analysis, measured)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    return out_path


def _readme(wb, analysis, work, measured, usage_meta) -> None:
    ws = wb.create_sheet("Read me")
    for col, width in zip("ABCD", (34, 15, 62, 52)):
        ws.column_dimensions[col].width = width

    ws["A1"] = f"Three follow-up requests — HubSpot account {analysis.get('portal_id')}"
    ws["A1"].font = TITLE
    ws["A2"] = (f"Measured {str(usage_meta.get('measured_at') or '')[:10]}. Fill rate is exact; "
                f"last-written is sampled from the {usage_meta.get('sample_size')} most recently "
                "modified records per object, so a date is a floor, never a ceiling.")
    ws["A2"].font = NOTE

    rows = [
        ("", "", "", ""),
        ("Request", "Verdict", "What was found", "Where to look"),
        ("1. Stale = no enrolments in a year", "Cannot be built",
         "HubSpot exposes no enrolment data to the API. Automation writes name the enrolment, "
         "not the workflow, and nothing resolves one to the other.",
         "Tab: 1. Why enrolment fails"),
        ("2. Fill rate on unused fields", "Done",
         f"All {len(analysis['properties'])} fields carry an exact count of how many records "
         "hold a value.", "Tabs: 2+3 Flagged fields · All fields"),
        ("3. When a field was last written", "Done",
         "Every field carries its most recent write and what caused it — automation, an "
         "integration, a form, an import or a person.", "Tabs: 2+3 Flagged fields · All fields"),
    ]
    for r in rows:
        ws.append(list(r))
    for cell in ws[5]:
        if cell.value:
            cell.fill, cell.font = HEAD_FILL, HEAD_FONT
    for row in ws.iter_rows(min_row=6, max_row=8):
        for cell in row:
            cell.font = BODY
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    p6 = work["p6"]
    groups = {"keep": 0, "judge": 0, "safe": 0}
    for r in p6:
        groups[_group(r["verdict"])] += 1

    ws.append([])
    ws.append(["What the measurement changed"])
    ws.cell(row=ws.max_row, column=1).font = SECTION
    ws.append(["Group", "Fields", "What it means", ""])
    for cell in ws[ws.max_row]:
        if cell.value:
            cell.fill, cell.font = HEAD_FILL, HEAD_FONT

    summary = [
        ("Empty or nearly empty", groups["safe"],
         "Nothing references them and nothing fills them. Safe to archive."),
        ("Written in the last 12 months", groups["keep"],
         "Something is actively filling these. Leave alone — this is the group the original "
         "advice would have wrongly archived."),
        ("Written, but longer ago", groups["judge"],
         "Judgement, with the date and the source in front of you."),
    ]
    for name, n, meaning in summary:
        ws.append([name, n, meaning, ""])
        row = ws.max_row
        ws.cell(row=row, column=1).font = BODY
        ws.cell(row=row, column=2).font = Font(name=FONT, size=10, bold=True)
        ws.cell(row=row, column=3).font = BODY
        ws.cell(row=row, column=3).alignment = Alignment(vertical="top", wrap_text=True)
        key = {"Empty or nearly empty": "safe",
               "Written in the last 12 months": "keep"}.get(name, "judge")
        ws.cell(row=row, column=1).fill = VERDICT_FILL[key]

    ws.append([])
    ws.append(["This file is a reference, not a worklist — the columns to fill in live on the "
               "P6 tab of the full inventory workbook."])
    ws.cell(row=ws.max_row, column=1).font = NOTE


def _request1(wb, work) -> None:
    ws = _sheet(
        wb, "1. Why enrolment fails",
        ["Method", "Endpoint tested", "HubSpot returned", "What it means"],
        [10, 52, 17, 62],
        "Request 1 — every route to workflow enrolment data, and what each returned. "
        "Recorded so the conclusion can be re-checked rather than taken on trust.",
    )
    for method, path, status, meaning in ENDPOINT_EVIDENCE:
        ws.append([method, path, status, meaning])
    _finish(ws)

    ws.append([])
    ws.append(["", "Conclusion", "",
               "Workflow-level activity cannot be measured through the API. Field-level activity "
               "can, and is on the next two tabs. Keep P4 on last-edited: imperfect, but the only "
               "workflow-level signal HubSpot exposes."])
    row = ws.max_row
    ws.cell(row=row, column=2).font = SECTION
    ws.cell(row=row, column=4).font = BODY
    ws.cell(row=row, column=4).alignment = Alignment(vertical="top", wrap_text=True)


def _request23(wb, work) -> None:
    ws = _sheet(
        wb, "2+3. Flagged fields",
        ["Field", "Verdict", "Fill rate", "Records with a value", "Last written",
         "Last written by", "Everything seen writing it", "Object", "Internal name", "Link"],
        [32, 34, 10, 17, 13, 20, 30, 14, 32, 17],
        "Requests 2 and 3 — the 332 fields the audit flagged as referenced by no workflow, form "
        "or list, now with fill rate and last-written. Sorted most recently written first: the "
        "rows where a decision could go wrong are at the top.",
    )
    for r in work["p6"]:
        ws.append([
            r["name"], r["verdict"],
            (r["fill_pct"] / 100) if r.get("fill_pct") is not None else "",
            r["filled"] if r.get("filled") is not None else "",
            r.get("last_written") or "", r.get("last_written_by") or "",
            ", ".join(r.get("written_by") or []), r["object"], r["label"], r["link"],
        ])
        ws.cell(row=ws.max_row, column=2).fill = VERDICT_FILL[_group(r["verdict"])]
    _finish(ws, percent_headers={"Fill rate"})


def _all_fields(wb, analysis, measured) -> None:
    ws = _sheet(
        wb, "All fields measured",
        ["Field", "Object", "Custom?", "Fill rate", "Records with a value", "Last written",
         "Last written by", "Referenced by automation?", "Internal name", "Link"],
        [32, 15, 9, 10, 17, 13, 20, 20, 32, 17],
        "Every field in the account with the same three measurements, whether or not the audit "
        "flagged it. Useful for checking a specific field rather than working through a list.",
    )
    for p in analysis["properties"]:
        u = measured.get(p["key"]) or {}
        ws.append([
            p.get("display") or p.get("label") or p["name"],
            p["object_type"],
            "no" if p["hubspot_defined"] else "yes",
            (u["fill_pct"] / 100) if u.get("fill_pct") is not None else "",
            u.get("filled") if u.get("filled") is not None else "",
            u.get("last_written") or "",
            u.get("last_written_by") or "",
            "yes" if p["usage_score"] else "no",
            p["key"], p["link"],
        ])
    _finish(ws, percent_headers={"Fill rate"})
