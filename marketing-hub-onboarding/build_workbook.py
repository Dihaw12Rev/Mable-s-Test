"""Build Marketing_Hub_Onboarding_Process.xlsx from process_data.py.

Run:  python3 build_workbook.py
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

import process_data as d

OUT = Path(__file__).with_name("Marketing_Hub_Onboarding_Process.xlsx")

FONT = "Arial"
NAVY = "1F3A5F"
TEAL = "2E7D7A"
PALE = "EEF3F7"
YELLOW = "FFF4C2"
BAR = "2E7D7A"

thin = Side(style="thin", color="D5DCE3")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

PHASE_NAME = {p["id"]: p["name"] for p in d.PHASES}


def style_header(ws, row, ncols, fill=NAVY):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.alignment = CENTER
        cell.border = BORDER
    ws.row_dimensions[row].height = 30


def style_body(ws, first_row, last_row, ncols):
    for r in range(first_row, last_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name=FONT, size=10)
            cell.alignment = WRAP
            cell.border = BORDER


def title(ws, text, subtitle):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=14, color=NAVY)
    ws["A2"] = subtitle
    ws["A2"].font = Font(name=FONT, italic=True, size=10, color="555555")


def widths(ws, values):
    for i, w in enumerate(values, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def table(ws, header_row, headers, rows, col_widths):
    for c, h in enumerate(headers, start=1):
        ws.cell(row=header_row, column=c, value=h)
    style_header(ws, header_row, len(headers))
    for r, row in enumerate(rows, start=header_row + 1):
        for c, v in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=v)
    last = header_row + len(rows)
    style_body(ws, header_row + 1, last, len(headers))
    widths(ws, col_widths)
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(headers))}{last}"
    return last


def start_here(wb):
    ws = wb.active
    ws.title = "Start Here"
    title(ws, "RevGravy · Marketing Hub Onboarding Process (draft v1)",
          "Built from the FigJam session. Day 0 = deal reaches 'Start Payment Received'. Program assumed to be "
          f"{d.PROGRAM_DAYS} days.")
    rows = [
        ("Roadmap", "Phases on a week-by-week timeline, mapped to the FigJam stickies."),
        ("Task Template", "Every task: owner, client-facing or not, start/due day, dependency, where it lives in HubSpot, automation."),
        ("Intake Form", "What we ask the customer after the sale (only what pre-sale didn't capture)."),
        ("Tech Setup", "Marketing Hub technical setup checklist with Starter / Pro / Enterprise flags."),
        ("Training", "Training modules by audience and timing."),
        ("Comms", "Every customer touchpoint, including the weekly update template."),
        ("Tool Fit", "HubSpot Work vs Projects vs Tickets scoring and the recommendation."),
        ("HubSpot Build Spec", "Pipelines, properties, workflows and the HubSpot Work workspace to build."),
        ("Open Questions", "Decisions needed from you / your boss. Yellow cells are for answers."),
    ]
    ws["A4"] = "Tab"
    ws["B4"] = "What's in it"
    style_header(ws, 4, 2)
    for i, (tab, desc) in enumerate(rows, start=5):
        ws.cell(row=i, column=1, value=tab)
        ws.cell(row=i, column=2, value=desc)
    style_body(ws, 5, 4 + len(rows), 2)

    r = 6 + len(rows)
    ws.cell(row=r, column=1, value="Role")
    ws.cell(row=r, column=2, value="Responsibility")
    style_header(ws, r, 2)
    for i, (role, desc) in enumerate(d.ROLES.items(), start=r + 1):
        ws.cell(row=i, column=1, value=role)
        ws.cell(row=i, column=2, value=desc)
    style_body(ws, r + 1, r + len(d.ROLES), 2)

    r = r + len(d.ROLES) + 2
    ws.cell(row=r, column=1, value="Legend")
    ws.cell(row=r, column=1).font = Font(name=FONT, bold=True, size=11, color=NAVY)
    ws.cell(row=r + 1, column=1, value="Yellow cell")
    ws.cell(row=r + 1, column=1).fill = PatternFill("solid", fgColor=YELLOW)
    ws.cell(row=r + 1, column=2, value="Edit me: assumptions and answers you should confirm or change.")
    ws.cell(row=r + 2, column=1, value="■ in Roadmap")
    ws.cell(row=r + 2, column=2, value="Calculated from the Start/End day columns. Change the days and the bars move.")
    for rr in (r + 1, r + 2):
        for c in (1, 2):
            ws.cell(row=rr, column=c).font = Font(name=FONT, size=10)
    widths(ws, [24, 110])


def gantt_columns(ws, header_row, first_col, start_col_letter, end_col_letter, first_data, last_data):
    """Week buckets from pre-sale to 90+; formulas mark where each row is active."""
    buckets = [("Pre-sale", -60, -1)] + [(f"W{w}", w * 7, w * 7 + 6) for w in range(13)] + [("90+", 91, 400)]
    for i, (label, lo, hi) in enumerate(buckets):
        col = first_col + i
        letter = get_column_letter(col)
        ws.cell(row=header_row - 2, column=col, value=lo)
        ws.cell(row=header_row - 1, column=col, value=hi)
        ws.cell(row=header_row, column=col, value=label)
        for rr in (header_row - 2, header_row - 1):
            ws.cell(row=rr, column=col).font = Font(name=FONT, size=8, color="999999")
            ws.cell(row=rr, column=col).alignment = CENTER
        ws.column_dimensions[letter].width = 5.5
        for r in range(first_data, last_data + 1):
            ws.cell(row=r, column=col,
                    value=f'=IF(AND(${start_col_letter}{r}<={letter}${header_row - 1},'
                          f'${end_col_letter}{r}>={letter}${header_row - 2}),"■","")')
            ws.cell(row=r, column=col).alignment = CENTER
            ws.cell(row=r, column=col).border = BORDER
            ws.cell(row=r, column=col).font = Font(name=FONT, size=10, color=BAR)
    last_letter = get_column_letter(first_col + len(buckets) - 1)
    rng = f"{get_column_letter(first_col)}{first_data}:{last_letter}{last_data}"
    ws.conditional_formatting.add(
        rng, CellIsRule(operator="equal", formula=['"■"'], fill=PatternFill("solid", fgColor=BAR)))
    return first_col + len(buckets) - 1


def roadmap(wb):
    ws = wb.create_sheet("Roadmap")
    title(ws, "Roadmap", "Rows 4–5 hold each week's day range (small grey numbers). Bars are formulas on Start/End day.")
    headers = ["Phase", "Name", "FigJam stage(s)", "Start day", "End day", "Goal", "What the client sees", "Exit criteria"]
    hr = 6
    rows = [(p["id"], p["name"], p["figjam"], p["start"], p["end"], p["goal"], p["client_sees"], p["exit"])
            for p in d.PHASES]
    last = table(ws, hr, headers, rows, [7, 20, 30, 8, 8, 40, 40, 40])
    for r in range(hr + 1, last + 1):
        for c in (4, 5):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=YELLOW)
            ws.cell(row=r, column=c).alignment = CENTER
    lastcol = gantt_columns(ws, hr, len(headers) + 1, "D", "E", hr + 1, last)
    style_header(ws, hr, lastcol)
    ws.auto_filter.ref = None
    ws.freeze_panes = "C7"


def task_template(wb):
    ws = wb.create_sheet("Task Template")
    title(ws, "Task Template", "One row per task. Duration and Gantt are formulas. Filter by Phase, Owner or Client-facing.")
    headers = ["ID", "Phase", "Task", "Details / definition of done", "Owner", "Client-facing", "Start day",
               "Due day", "Duration (days)", "Depends on", "Where it lives in HubSpot", "Automation"]
    hr = 6
    rows = []
    for t in d.TASKS:
        tid, ph, task, det, owner, cf, s, e, dep, where, auto = t
        rows.append((tid, f"{ph} · {PHASE_NAME[ph]}", task, det, owner, cf, s, e, None, dep, where, auto))
    last = table(ws, hr, headers, rows, [6, 20, 30, 55, 12, 9, 7, 7, 9, 11, 26, 26])
    for r in range(hr + 1, last + 1):
        ws.cell(row=r, column=9, value=f"=H{r}-G{r}+1")
        for c in (6, 7, 8, 9):
            ws.cell(row=r, column=c).alignment = CENTER
        for c in (7, 8):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=YELLOW)
    ws.conditional_formatting.add(
        f"F{hr + 1}:F{last}",
        CellIsRule(operator="equal", formula=['"Yes"'], fill=PatternFill("solid", fgColor="DCEFEA")))
    dv = DataValidation(type="list", formula1='"' + ",".join(d.ROLES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"E{hr + 1}:E{last}")
    lastcol = gantt_columns(ws, hr, len(headers) + 1, "G", "H", hr + 1, last)
    style_header(ws, hr, lastcol)
    ws.auto_filter.ref = f"A{hr}:{get_column_letter(len(headers))}{last}"
    ws.freeze_panes = "D7"

    # Summary by owner
    r = last + 3
    ws.cell(row=r, column=3, value="Tasks by owner")
    ws.cell(row=r, column=3).font = Font(name=FONT, bold=True, size=11, color=NAVY)
    ws.cell(row=r + 1, column=3, value="Owner")
    ws.cell(row=r + 1, column=4, value="# tasks")
    ws.cell(row=r + 1, column=5, value="Client-facing")
    style_header(ws, r + 1, 5)
    for c in (1, 2):
        ws.cell(row=r + 1, column=c).fill = PatternFill(fill_type=None)
        ws.cell(row=r + 1, column=c).border = Border()
    for i, role in enumerate(d.ROLES, start=r + 2):
        ws.cell(row=i, column=3, value=role)
        ws.cell(row=i, column=4, value=f'=COUNTIF($E${hr + 1}:$E${last},C{i})')
        ws.cell(row=i, column=5, value=f'=COUNTIFS($E${hr + 1}:$E${last},C{i},$F${hr + 1}:$F${last},"Yes")')
        for c in (3, 4, 5):
            ws.cell(row=i, column=c).font = Font(name=FONT, size=10)
            ws.cell(row=i, column=c).border = BORDER
    tot = r + 2 + len(d.ROLES)
    ws.cell(row=tot, column=3, value="Total")
    ws.cell(row=tot, column=4, value=f"=SUM(D{r + 2}:D{tot - 1})")
    ws.cell(row=tot, column=5, value=f"=SUM(E{r + 2}:E{tot - 1})")
    for c in (3, 4, 5):
        ws.cell(row=tot, column=c).font = Font(name=FONT, size=10, bold=True)
        ws.cell(row=tot, column=c).border = BORDER


def simple_tab(wb, name, subtitle, headers, rows, col_widths):
    ws = wb.create_sheet(name)
    title(ws, name, subtitle)
    table(ws, 4, headers, rows, col_widths)
    return ws


def tool_fit(wb):
    ws = wb.create_sheet("Tool Fit")
    title(ws, "Tool Fit: HubSpot Work vs Projects vs Tickets",
          "Score 0 = poor, 1 = workable, 2 = strong. Edit the yellow scores; totals are formulas.")
    headers = ["Criterion", "Work score", "HubSpot Work", "Projects score", "Projects object", "Tickets score", "Tickets"]
    hr = 4
    rows = []
    for crit, w, p, t in d.TOOL_FIT:
        rows.append((crit, w[0], w[1], p[0], p[1], t[0], t[1]))
    last = table(ws, hr, headers, rows, [32, 8, 38, 8, 38, 8, 38])
    for r in range(hr + 1, last + 1):
        for c in (2, 4, 6):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=YELLOW)
            ws.cell(row=r, column=c).alignment = CENTER
    tr = last + 1
    ws.cell(row=tr, column=1, value="Total (max " + str(2 * len(d.TOOL_FIT)) + ")")
    for c in (2, 4, 6):
        L = get_column_letter(c)
        ws.cell(row=tr, column=c, value=f"=SUM({L}{hr + 1}:{L}{last})")
        ws.cell(row=tr, column=c).alignment = CENTER
    for c in range(1, 8):
        ws.cell(row=tr, column=c).font = Font(name=FONT, bold=True, size=10)
        ws.cell(row=tr, column=c).fill = PatternFill("solid", fgColor=PALE)
        ws.cell(row=tr, column=c).border = BORDER
    ws.conditional_formatting.add(
        f"B{hr + 1}:F{last}",
        FormulaRule(formula=[f'AND(ISNUMBER(B{hr + 1}),B{hr + 1}=0)'], font=Font(color="B42318", bold=True)))
    ws.auto_filter.ref = None

    r = tr + 3
    ws.cell(row=r, column=1, value="Recommendation: use each tool for the job it's best at")
    ws.cell(row=r, column=1).font = Font(name=FONT, bold=True, size=12, color=NAVY)
    ws.cell(row=r + 1, column=1, value="Tool")
    ws.cell(row=r + 1, column=3, value="Its job in the onboarding")
    ws.merge_cells(start_row=r + 1, start_column=3, end_row=r + 1, end_column=7)
    style_header(ws, r + 1, 7, fill=TEAL)
    for i, (tool, job) in enumerate(d.TOOL_VERDICT, start=r + 2):
        ws.cell(row=i, column=1, value=tool)
        ws.cell(row=i, column=3, value=job)
        ws.merge_cells(start_row=i, start_column=3, end_row=i, end_column=7)
        ws.row_dimensions[i].height = 42
        for c in range(1, 8):
            ws.cell(row=i, column=c).font = Font(name=FONT, size=10, bold=(c == 1))
            ws.cell(row=i, column=c).alignment = WRAP
            ws.cell(row=i, column=c).border = BORDER
    note = r + 3 + len(d.TOOL_VERDICT)
    ws.cell(row=note, column=1,
            value="Scores for HubSpot Work are based on public beta descriptions (Oct 2026) and should be re-checked "
                  "once the portal is enrolled in the beta.")
    ws.cell(row=note, column=1).font = Font(name=FONT, italic=True, size=9, color="555555")


def open_questions(wb):
    ws = wb.create_sheet("Open Questions")
    title(ws, "Open Questions", "Answer in the yellow column. Each answer changes the part of the design listed.")
    headers = ["#", "Topic", "Question", "What it changes", "Answer"]
    rows = [(i, t, q, w, "") for i, (t, q, w) in enumerate(d.OPEN_QUESTIONS, start=1)]
    last = table(ws, 4, headers, rows, [5, 12, 70, 34, 50])
    for r in range(5, last + 1):
        ws.cell(row=r, column=5).fill = PatternFill("solid", fgColor=YELLOW)


def main():
    wb = Workbook()
    start_here(wb)
    roadmap(wb)
    task_template(wb)
    simple_tab(wb, "Intake Form", "Post-sale intake. 'Captured pre-sale' items are pre-filled from the deal and only confirmed.",
               ["Section", "Question", "Field type", "Required", "Captured pre-sale?", "Why we ask", "Maps to"],
               d.INTAKE, [16, 50, 34, 9, 14, 40, 32])
    simple_tab(wb, "Tech Setup", "Tier: S = all tiers (Starter+), P = Professional+, E = Enterprise only.",
               ["Area", "Item", "Details", "Tier", "Task ID", "Owner"],
               d.TECH_SETUP, [14, 36, 60, 6, 8, 20])
    simple_tab(wb, "Training", "Each module is short and timed to when the feature ships.",
               ["Module", "Audience", "Content", "Format", "When", "Length"],
               d.TRAINING, [30, 26, 50, 30, 30, 10])
    simple_tab(wb, "Comms", "Every customer-facing touchpoint, in order.",
               ["Touchpoint", "Timing", "Channel", "Owner", "Content"],
               d.COMMS, [26, 22, 22, 22, 80])
    tool_fit(wb)
    simple_tab(wb, "HubSpot Build Spec", "What to build in the portal once the design is approved.",
               ["Area", "Item", "Spec"], d.BUILD_SPEC, [18, 38, 110])
    open_questions(wb)
    for ws in wb.worksheets:
        ws.sheet_view.zoomScale = 100
        ws.sheet_properties.tabColor = NAVY if ws.title in ("Start Here", "Open Questions") else TEAL
    wb.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
