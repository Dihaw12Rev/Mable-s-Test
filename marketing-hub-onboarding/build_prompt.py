"""Build the exact HubSpot Work prompt from process_data.py.

The prompt builds the template project, its sections and tasks (with setup
items as subtasks), columns, board and views, the requests table, the
portfolio, and the agents. No documents or forms.

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

new_customer = "\n".join(f"{i}. {step}" for i, step in enumerate(d.NEW_CUSTOMER_STEPS, start=1))
visible = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" not in n)
hidden = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" in n)
due_rule = (f"Due date = Project Day 0 + Due day. For programs shorter than 90 days, tasks with a Due day above {d.FIXED_UNTIL_DAY} "
            f"are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: "
            f"Due day − 90 + Program length. Tasks in section P0 get no date. If Project Day 0 is empty, Due date stays empty.")
task_columns = "\n".join(f"- {c} ({t}): {n}" for c, t, n in d.WORK_TASK_COLUMNS)
views = "\n".join(f"- {v}: {s}" for v, s in d.WORK_VIEWS)
request_columns = "; ".join(f"{c} ({t})" for c, t in d.WORK_REQUEST_COLUMNS)
request_classes = "\n".join(f"- {u}: {w} {t} Price: {p}." for u, w, t, p in d.REQUEST_CLASSES)
portfolio_columns = "; ".join(f"{c} ({t})" for c, t in d.WORK_PORTFOLIO_COLUMNS)
portfolio_views = "\n".join(f"- {v}: {s}" for v, s in d.WORK_PORTFOLIO_VIEWS)
statuses = ", ".join(d.WORK_STATUSES)
agents = "\n".join(f"- {n}. Trigger: {t}. What it does: {w}" for n, t, w in d.WORK_AGENTS)
n_tasks = len(d.TASKS)
n_sub = sum(len(v) for v in subtasks.values())

PROMPT = f"""Build a workspace called "Client Onboarding" for RevGravy, a HubSpot consultancy. It holds the structure we use to run every Marketing Hub onboarding. Build only what is described below: projects, task sections, tasks, subtasks, columns, board, views and agents. Do not create documents or forms.

HOW WE WILL USE IT
- Day 0 is the day the customer's deal reaches "Start Payment Received" in our Sales Pipeline.
- Programs last 60 to 90 days. The task days below are for a 90-day program.
- Projects have no custom fields, so each customer's details live on their row in the Customers table. The Customer column holds the exact name of the customer's project, and that is how the two are matched.
- For each new customer:
{new_customer}

PROJECT 1: "Marketing Hub Onboarding (Template)"

Table "Tasks" with these columns, in this order:
{task_columns}

Board statuses, in this order: {statuses}. Every task starts as "Not started".

Main table: show {visible}. Hide {hidden}.

Due date formula: {due_rule} Leave Project Day 0 and Program length empty in the template.

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
Views and reports:
{portfolio_views}

AGENTS
Every agent only drafts, fills dates or flags. None of them sends anything to a customer or changes a deal. Agents find a customer's project through the Customers row: its Customer value is the project's exact name.
{agents}

CHECK
When you show me the plan, confirm the counts: 2 projects, {len(d.PHASES)} sections, {n_tasks} tasks, {n_sub} subtasks, {len(d.WORK_VIEWS)} views on Tasks, 1 Requests table, {len(d.WORK_AGENTS)} agents. Show me the plan and wait for my approval before you create anything.
"""

# Follow-up prompt for a workspace that was already built from the v2 prompt (no agents yet).
CHANGED_TASKS = ["1.01", "1.02", "8.01", "8.02", "8.03", "9.04"]   # changed since the v2 build
changed = "\n".join(
    f"- {t[0]} {t[2]}: Owner role = {t[4]}. Definition of done = \"{t[3]}\""
    for t in d.TASKS if t[0] in CHANGED_TASKS)

UPDATE = f"""Update the existing "Client Onboarding" workspace. Don't recreate or duplicate anything that already exists; only make the changes below.

1. TASK IDS AND COLUMNS
In the Tasks table of "Marketing Hub Onboarding (Template)", make sure every task has its Task ID filled (0.01 to 9.05, matching the order of the tasks). In the Main table view, show these columns in this order: {visible}. Hide {hidden}.

2. CHECK THE DUE DATE FORMULA
Make sure the Due date formula follows this rule, and fix it if it doesn't: {due_rule}

3. TASK CHANGES
The Architect now runs the "what's next" call, and customer details live on the Customers table. Update these tasks:
{changed}

4. AGENTS
Add these agents. Every agent only drafts, fills dates or flags. None of them sends anything to a customer or changes a deal. Agents find a customer's project through the Customers row: its Customer value is the project's exact name.
{agents}

Show me the plan and wait for my approval before you change anything. When you're done, confirm: {len(d.TASKS)} tasks with a Task ID, {len(CHANGED_TASKS)} tasks updated, {len(d.WORK_AGENTS)} agents.
"""

GUIDE = f"""# HubSpot Work prompt: Marketing Hub Onboarding

`hubspot-work-prompt.txt` has the exact text to paste into HubSpot Work. It builds the template project ({len(d.PHASES)} sections, {n_tasks} tasks, {n_sub} subtasks), the board and views, a Requests table, the Onboarding Portfolio with its Customers table, and {len(d.WORK_AGENTS)} agents. No documents or forms.

It's generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

There are two prompts:

- `hubspot-work-prompt.txt` builds everything from scratch, in a new workspace.
- `hubspot-work-update-prompt.txt` is for the workspace already built from the earlier prompt. paste it in that workspace's chat. It puts Task IDs first, checks the Due date formula, updates 6 tasks, and adds the agents.

## How to use the full prompt

1. Open HubSpot Work and start a new workspace from a blank prompt.
2. Paste everything in `hubspot-work-prompt.txt`.
3. HubSpot Work shows a plan first. Check the counts against the CHECK line at the end, then approve.
4. For each new customer:
""" + "\n".join(f"   {i}. {step}" for i, step in enumerate(d.NEW_CUSTOMER_STEPS, start=1)) + """

Agents spend HubSpot Credits. The Delay Flagger and Portfolio Sync run every weekday, so check the credit balance before turning them on.

If HubSpot Work says the prompt is too long, paste everything up to the line "Create these sections and tasks" first. Then send the sections in two or three messages, each starting with "Add these sections and tasks to the Tasks table in the template project:".

## The prompt

```text
{PROMPT}```
"""

(HERE / "hubspot-work-prompt.txt").write_text(PROMPT, encoding="utf-8")
(HERE / "hubspot-work-update-prompt.txt").write_text(UPDATE, encoding="utf-8")
(HERE / "hubspot-work-prompt.md").write_text(GUIDE + f"""
## The update prompt (for the workspace you already built)

```text
{UPDATE}```
""", encoding="utf-8")
print(f"Update prompt: {len(UPDATE):,} characters")
print(f"Prompt: {len(PROMPT):,} characters, {n_tasks} tasks, {n_sub} subtasks, {len(d.WORK_AGENTS)} agents")
