"""Build the exact HubSpot Work prompt from process_data.py.

The prompt only builds structure: the template project, its sections and
tasks (with setup items as subtasks), columns, board and views, the requests
table, and the portfolio. No agents, documents or forms.

Writes hubspot-work-prompt.txt (the text to paste) and hubspot-work-prompt.md
(the same text plus how to use it).

Run:  python3 build_prompt.py
"""
from collections import defaultdict
from pathlib import Path

import process_data as d

HERE = Path(__file__).parent

subtasks = defaultdict(list)
for area, item, det, tier, tid, owner in d.TECH_SETUP:
    subtasks[tid].append(item + (" (Enterprise only)" if tier == "Ent only" else ""))


def task_line(t):
    tid, ph, task, det, owner, cf, s, e, dep, where, rep = t
    days = "before Day 0, check at the handoff" if ph == "P0" else (f"Day {s}" if s == e else f"Day {s}–{e}")
    bits = [f"{tid} {task}", f"Owner: {owner}", f"Client-facing: {cf}", days]
    if rep:
        bits.append(f"Repeats: {rep}")
    if dep:
        bits.append(f"Depends on: {dep}")
    line = "- " + " | ".join(bits) + f"\n  Done when: {det}"
    if subtasks.get(tid):
        line += "\n  Subtasks: " + "; ".join(subtasks[tid])
    return line


sections = []
for p in d.PHASES:
    tasks = "\n".join(task_line(t) for t in d.TASKS if t[1] == p["id"])
    sections.append(f"Section {p['id']} · {p['name']} (Day {p['start']} to {p['end']})\n{tasks}")
sections = "\n\n".join(sections)

project_fields = "; ".join(f"{f} ({t})" for f, t in d.WORK_PROJECT_FIELDS)
task_columns = "\n".join(f"- {c} ({t}): {n}" for c, t, n in d.WORK_TASK_COLUMNS)
views = "\n".join(f"- {v}: {s}" for v, s in d.WORK_VIEWS)
request_columns = "; ".join(f"{c} ({t})" for c, t in d.WORK_REQUEST_COLUMNS)
request_classes = "\n".join(f"- {u}: {w} {t} Price: {p}." for u, w, t, p in d.REQUEST_CLASSES)
portfolio_columns = "; ".join(f"{c} ({t})" for c, t in d.WORK_PORTFOLIO_COLUMNS)
portfolio_views = "\n".join(f"- {v}: {s}" for v, s in d.WORK_PORTFOLIO_VIEWS)
statuses = ", ".join(d.WORK_STATUSES)
n_tasks = len(d.TASKS)
n_sub = sum(len(v) for v in subtasks.values())

PROMPT = f"""Build a workspace called "Client Onboarding" for RevGravy, a HubSpot consultancy. It holds the structure we use to run every Marketing Hub onboarding. Only build the structure described below: projects, task sections, tasks, subtasks, columns, board and views. Do not create agents, documents or forms.

HOW WE WILL USE IT
- Each customer gets a copy of the template project, named "<Client> · Marketing Hub Onboarding".
- Day 0 is the day the customer's deal reaches "Start Payment Received" in our Sales Pipeline.
- Programs last 60 to 90 days. The task days below are for a 90-day program.

PROJECT 1: "Marketing Hub Onboarding (Template)"

Project fields: {project_fields}.

Table "Tasks" with these columns:
{task_columns}

Board statuses, in this order: {statuses}. Every task starts as "Not started".

Due date rule: Due date = project Start date + Due day. For programs shorter than 90 days, tasks with a Due day above {d.FIXED_UNTIL_DAY} are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: Due day − 90 + Program length. Tasks in section P0 get no date. If formula columns are supported, make Due date a formula that follows this rule; if not, leave it empty.

Views on the Tasks table:
{views}

Create these sections and tasks, in this order. Put each task in its section and fill Task ID, Owner role, Client-facing, Start day, Due day, Repeats, Depends on and Definition of done ("Done when") from its line. Add the "Subtasks" as a checklist of subtasks under that task.

{sections}

Table "Requests" (in the same project) with these columns: {request_columns}.
Views on Requests: "Board by urgency" (columns = Urgency) and "Open requests" (Status not Done or Parked, sorted by Due date).
Use these as the descriptions of the Urgency options:
{request_classes}

PROJECT 2: "Onboarding Portfolio"

Table "Customers", one row per customer, with these columns: {portfolio_columns}.
Views:
{portfolio_views}

CHECK
When you show me the plan, confirm the counts: 2 projects, {len(d.PHASES)} sections, {n_tasks} tasks, {n_sub} subtasks, {len(d.WORK_VIEWS)} views on Tasks, 1 Requests table. Show me the plan and wait for my approval before you create anything.
"""

GUIDE = f"""# HubSpot Work prompt: Marketing Hub Onboarding

`hubspot-work-prompt.txt` has the exact text to paste into HubSpot Work. It only builds structure: the template project, {len(d.PHASES)} sections, {n_tasks} tasks, {n_sub} subtasks, the board and views, a Requests table and a Portfolio for Phil. No agents, documents or forms.

It's generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

## How to use it

1. Open HubSpot Work and start a new workspace from a blank prompt.
2. Paste everything in `hubspot-work-prompt.txt`.
3. HubSpot Work shows a plan first. Check the counts against the CHECK line at the end, then approve.
4. For each new customer, duplicate the template project, rename it, fill the project fields, and add a row to the Portfolio.

If HubSpot Work says the prompt is too long, paste everything up to the line "Create these sections and tasks" first. Then send the sections in two or three messages, each starting with "Add these sections and tasks to the Tasks table in the template project:".

## The prompt

```text
{PROMPT}```
"""

(HERE / "hubspot-work-prompt.txt").write_text(PROMPT, encoding="utf-8")
(HERE / "hubspot-work-prompt.md").write_text(GUIDE, encoding="utf-8")
print(f"Prompt: {len(PROMPT):,} characters, {n_tasks} tasks, {n_sub} subtasks")
