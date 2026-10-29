"""Build the HubSpot Work prompts from process_data.py.

Writes:
- hubspot-work-redesign-prompt.txt  switch the workspace already built to shared tables (paste in its chat)
- hubspot-work-prompt.txt           build everything from scratch in a new workspace
- hubspot-work-agent-prompts.md     one prompt per agent, for HubSpot Work's agent builder
- hubspot-work-prompt.md            how to use all of the above

Run:  python3 build_prompt.py
"""
from collections import defaultdict
from pathlib import Path

import process_data as d

HERE = Path(__file__).parent
(HERE / "hubspot-work-update-prompt.txt").unlink(missing_ok=True)   # superseded by the redesign prompt

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


def bullets(rows, fmt):
    return "\n".join(fmt(*r) for r in rows)


sections = "\n\n".join(
    f"Section {p['id']} · {p['name']} (Day {p['start']} to {p['end']})\n" + "\n".join(task_line(t) for t in d.TASKS if t[1] == p["id"])
    for p in d.PHASES)

statuses = ", ".join(d.WORK_STATUSES)
task_columns = bullets(d.WORK_TASK_COLUMNS, lambda c, t, n: f"- {c} ({t}): {n}")
visible = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" not in n)
hidden = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" in n)
visible_ct = visible.replace("Task ID, Task,", "Task ID, Customer, Task,")
views = bullets(d.WORK_VIEWS, lambda v, s: f"- {v}: {s}")
template_views = bullets([v for v in d.WORK_VIEWS if v[0] != "By customer"],
                         lambda v, s: f"- {v}: {s}".replace("Customer, ", "").replace("grouped by Customer", "grouped by Section"))
customers_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_PORTFOLIO_COLUMNS)
portfolio_views = bullets(d.WORK_PORTFOLIO_VIEWS, lambda v, s: f"- {v}: {s}")
request_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_REQUEST_COLUMNS)
request_classes = bullets(d.REQUEST_CLASSES, lambda u, w, t, p: f"- {u}: {w} {t} Price: {p}.")
update_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_UPDATE_COLUMNS)
update_views = bullets(d.WORK_UPDATE_VIEWS, lambda v, s: f"- {v}: {s}")
new_customer = "\n".join(f"{i}. {s}" for i, s in enumerate(d.NEW_CUSTOMER_STEPS, start=1))
due_rule = (f"Due date = Project Day 0 + Due day. For programs shorter than 90 days, tasks with a Due day above {d.FIXED_UNTIL_DAY} "
            f"are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: "
            f"Due day − 90 + Program length. Tasks in section P0 get no date. If Project Day 0 is empty, Due date stays empty.")
n_tasks = len(d.TASKS)
n_sub = sum(len(v) for v in subtasks.values())

PORTFOLIO_TABLES = f"""Table "Customers", one row per customer. Columns: {customers_cols}.
Views and reports:
{portfolio_views}

Table "Customer Task": every customer's tasks in one table. Same columns as the template's Tasks table (including the Due date formula, both helper columns, and subtasks), plus "Customer" (link to the Customers row) as the second column. Statuses: {statuses}.
Main table: show {visible_ct}. Hide {hidden}.
Views:
{views}
Leave it empty; the Task Generator fills it for each new customer.

Table "Request": every customer's requests. Columns: {request_cols}.
Views: "Board by urgency" (columns = Urgency) and "Open requests" (Status not Done or Parked, sorted by Due date).
Use these as the descriptions of the Urgency options:
{request_classes}

Table "Update": drafts the agents write for the Architect. Columns: {update_cols}.
Views:
{update_views}"""

CHANGED = ["1.01", "1.02"]
changed = "\n".join(f"- {t[0]}: Task = \"{t[2]}\". Owner role = {t[4]}. Definition of done = \"{t[3]}\""
                    for t in d.TASKS if t[0] in CHANGED)

REDESIGN = f"""Restructure the "Client Onboarding" workspace the way you recommended: shared tables linked to Customers, so agents work across all customers. Don't create agents; I'll create them in the agent builder. Don't create documents or forms. Don't delete anything that has rows.

1. TEMPLATE PROJECT
Keep "Marketing Hub Onboarding (Template)" and its Tasks table as the master task list. Nobody works in it; new customers' tasks get copied from it.
- Update these tasks:
{changed}
- Check that the Due date formula follows this rule, and fix it if it doesn't: {due_rule}
- If the template's Request table has no rows, remove it. Requests now live in the Onboarding Portfolio.

2. ONBOARDING PORTFOLIO PROJECT
Make it hold these four tables.

{PORTFOLIO_TABLES}

3. HOW WE'LL USE IT
{new_customer}

Show me the plan and wait for my approval before you change anything. When you're done, confirm: 4 tables in Onboarding Portfolio (Customers, Customer Task, Request, Update), {len(d.WORK_VIEWS)} views on Customer Task, 0 rows in Customer Task, and tasks 1.01 and 1.02 updated in the template.
"""

PROMPT = f"""Build a workspace called "Client Onboarding" for RevGravy, a HubSpot consultancy, to run every Marketing Hub onboarding. Build only the projects, tables, columns, views, sections, tasks and subtasks below. Don't create agents (I'll create them in the agent builder), documents or forms.

HOW WE'LL USE IT
- Day 0 is the day the customer's deal reaches "Start Payment Received" in our Sales Pipeline. Programs last 60 to 90 days; the task days below are for a 90-day program.
- All customers share the same tables, and each row links to its Customers row, so agents work across all customers.
{new_customer}

PROJECT 1: "Marketing Hub Onboarding (Template)"
The master task list. Nobody works in it; new customers' tasks get copied from it.

Table "Tasks" with these columns, in this order:
{task_columns}

Statuses, in this order: {statuses}. Every task starts as "Not started".
Main table: show {visible}. Hide {hidden}.
Due date formula: {due_rule} Leave Project Day 0 and Program length empty in the template.

Views:
{template_views}

Create these sections and tasks, in this order. Put each task in its section and fill Task ID, Owner role, Client-facing, Start day, Due day, Repeats, Depends on and Definition of done ("Done when") from its line. Add the "Subtasks" as a checklist of subtasks under that task.

{sections}

PROJECT 2: "Onboarding Portfolio"

{PORTFOLIO_TABLES}

CHECK
When you show me the plan, confirm: 2 projects; the template has {len(d.PHASES)} sections, {n_tasks} tasks and {n_sub} subtasks; Onboarding Portfolio has 4 tables (Customers, Customer Task, Request, Update) and Customer Task has {len(d.WORK_VIEWS)} views. Show me the plan and wait for my approval before you create anything.
"""

COMMON_RULE = "Only draft, fill fields or flag. Never send anything to a customer and never change a CRM deal."


def agent_prompt(a):
    lines = [f"Name: {a['name']}",
             "Where: \"Client Onboarding\" workspace, \"Onboarding Portfolio\" project. Tables: Customers, Customer Task, Request, Update. Each row in Customer Task, Request and Update links to its Customers row through the Customer column.",
             f"Trigger: {a['trigger']}",
             "What to do:"]
    lines += [f"{i}. {s}" for i, s in enumerate(a["steps"], start=1)]
    lines += ["Rules:"] + [f"- {r}" for r in a["rules"] + [COMMON_RULE]]
    return "\n".join(lines)


agent_blocks = []
for i, a in enumerate(d.WORK_AGENTS, start=1):
    start = f"Start from the sample **{a['sample']}** and replace its description with this." if a["sample"] else "Start from a blank agent."
    agent_blocks.append(f"## {i}. {a['name']}\n\n{a['summary']} {start}\n\n```text\n{agent_prompt(a)}\n```\n")

AGENTS_MD = f"""# HubSpot Work agent prompts

One prompt per agent for HubSpot Work's agent builder ("What kind of agent do you want to create?"). Create them only after the workspace has the shared tables (Customers, Customer Task, Request, Update).

Customer tasks are created by the task-seeding workflow (see the redesign prompt). The **Onboarding Task Generator** below is the agent version; use it only if the workflow can't be built. Test task creation with your next real customer before turning on the rest.

Agents spend HubSpot Credits. Delay Flagger and Portfolio Sync run every day.

""" + "\n".join(agent_blocks)

GUIDE = f"""# HubSpot Work prompts: Marketing Hub Onboarding

All of these are generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

| File | When to use it |
|---|---|
| `hubspot-work-redesign-prompt.txt` | Paste into the chat of the workspace you already built. It switches to shared tables linked to Customers, which is the setup HubSpot Work recommended so agents work across all customers. |
| `hubspot-work-agent-prompts.md` | {len(d.WORK_AGENTS)} prompts, one per agent, for the agent builder. Use them after the redesign. |
| `hubspot-work-prompt.txt` | Builds everything from scratch in a new workspace (no agents). |

## Why shared tables

HubSpot Work has no custom project fields, and copying a project doesn't copy its agents' workflows. With one project per customer, every agent would have to be set up again in each copy, and nothing could look across customers. With shared tables, each Customer Task, Request and Update row links to its Customers row, and one set of agents covers everyone.

## Order

1. Paste `hubspot-work-redesign-prompt.txt` in the workspace chat and approve the plan.
2. Make sure the task-seeding workflow exists (or create the Onboarding Task Generator agent from `hubspot-work-agent-prompts.md`).
3. Test it: add a Customers row "Test Co" with Start date today, Program length 60 and yourself as Architect. Expect {n_tasks} rows in Customer Task for Test Co, task 4.11 due in 20 days, 8.05 in 60, 9.05 in 240, P0 tasks undated, and Tasks created = Yes.
4. Create the other {len(d.WORK_AGENTS) - 1} agents.
5. Delete the Test Co row and its tasks. Share the workspace with Phil and the Architects.

## Redesign prompt

```text
{REDESIGN}```
"""

(HERE / "hubspot-work-redesign-prompt.txt").write_text(REDESIGN, encoding="utf-8")
(HERE / "hubspot-work-prompt.txt").write_text(PROMPT, encoding="utf-8")
(HERE / "hubspot-work-agent-prompts.md").write_text(AGENTS_MD, encoding="utf-8")
(HERE / "hubspot-work-prompt.md").write_text(GUIDE, encoding="utf-8")
print(f"Redesign prompt: {len(REDESIGN):,} characters")
print(f"Full prompt: {len(PROMPT):,} characters, {n_tasks} tasks, {n_sub} subtasks")
print(f"Agent prompts: {len(d.WORK_AGENTS)}, longest {max(len(agent_prompt(a)) for a in d.WORK_AGENTS):,} characters")
