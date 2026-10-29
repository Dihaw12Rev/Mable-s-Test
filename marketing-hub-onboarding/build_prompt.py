"""Build the HubSpot Work prompts from process_data.py.

Writes:
- hubspot-work-library-1-restructure.txt  turn the Marketing Hub template into the Task Library (Core + Marketing Hub)
- hubspot-work-library-2-sales-hub.txt    add the Sales Hub module to the Task Library
- hubspot-work-library-3-service-hub.txt  add the Service Hub module to the Task Library
- hubspot-work-library-4-customers.txt    Products purchased, Create tasks and Module columns
- hubspot-work-prompt.txt                 build everything from scratch in a new workspace
- hubspot-work-agent-prompts.md           one prompt per agent, for HubSpot Work's agent builder
- hubspot-work-prompt.md                  how to use all of the above

Run:  python3 build_prompt.py
"""
from collections import defaultdict
from pathlib import Path

import process_data as d

HERE = Path(__file__).parent
for old in ("hubspot-work-update-prompt.txt", "hubspot-work-redesign-prompt.txt"):   # superseded
    (HERE / old).unlink(missing_ok=True)

LIBRARY_PROJECT = "Onboarding Task Library"
LIBRARY_TABLE = "Task Library"
MODULE_NAME = {"Core": "Core", **{k: v for k, v in d.MODULES.items() if k != "Core"}}
TRAINING_FOR = {"T": "MH-6.02", "S": "SH-6.02", "V": "SV-6.02"}

subtasks = defaultdict(list)
for area, item, det, tier, tid, owner in d.TECH_SETUP:
    subtasks[tid].append(item + (" (Enterprise only)" if tier == "Ent only" else ""))
for module, *_ in d.TRAINING:
    subtasks[TRAINING_FOR[module[0]]].append(module)

phase_order = [p["id"] for p in d.PHASES]
module_order = list(d.MODULES)
ORDERED = [t for _, t in sorted(enumerate(d.TASKS), key=lambda it: (phase_order.index(it[1][1]), module_order.index(d.module_of(it[1][0])), it[0]))]
PHASE = {p["id"]: p for p in d.PHASES}


def module(tid):
    return MODULE_NAME[d.module_of(tid)]


def task_line(t):
    tid, ph, task, det, owner, cf, s, e, dep, where, rep = t
    days = "before Day 0, check at the handoff" if ph == "P0" else (f"Day {s}" if s == e else f"Day {s}–{e}")
    bits = [f"{tid} {task}", f"Module: {module(tid)}", f"Owner: {owner}", f"Client-facing: {cf}", days]
    if rep:
        bits.append(f"Repeats: {rep}")
    if dep:
        bits.append(f"Depends on: {dep}")
    line = "- " + " | ".join(bits) + f"\n  Done when: {det}"
    if subtasks.get(tid):
        line += "\n  Subtasks: " + "; ".join(subtasks[tid])
    return line


def sections_for(tasks):
    out = []
    for pid in phase_order:
        ts = [t for t in tasks if t[1] == pid]
        if ts:
            p = PHASE[pid]
            out.append(f"Section {pid} · {p['name']} (Day {p['start']} to {p['end']})\n" + "\n".join(task_line(t) for t in ts))
    return "\n\n".join(out)


def bullets(rows, fmt):
    return "\n".join(fmt(*r) for r in rows)


statuses = ", ".join(d.WORK_STATUSES)
task_columns = bullets(d.WORK_TASK_COLUMNS, lambda c, t, n: f"- {c} ({t}): {n}")
visible = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" not in n)
hidden = ", ".join(c for c, t, n in d.WORK_TASK_COLUMNS if "hidden" in n)
visible_ct = visible.replace("Task ID, Task,", "Task ID, Customer, Task,")
views = bullets(d.WORK_VIEWS, lambda v, s: f"- {v}: {s}")
library_views = bullets([v for v in d.WORK_VIEWS if v[0] in ("By section", "By module", "Board")],
                        lambda v, s: f"- {v}: {s}".replace("Customer, ", ""))
customers_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_PORTFOLIO_COLUMNS)
portfolio_views = bullets(d.WORK_PORTFOLIO_VIEWS, lambda v, s: f"- {v}: {s}")
request_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_REQUEST_COLUMNS)
request_classes = bullets(d.REQUEST_CLASSES, lambda u, w, t, p: f"- {u}: {w} {t} Price: {p}.")
update_cols = "; ".join(f"{c} ({t})" for c, t in d.WORK_UPDATE_COLUMNS)
update_views = bullets(d.WORK_UPDATE_VIEWS, lambda v, s: f"- {v}: {s}")
new_customer = "\n".join(f"{i}. {s}" for i, s in enumerate(d.NEW_CUSTOMER_STEPS, start=1))
products = ", ".join(d.PRODUCTS.values())
due_rule = (f"Due date = Project Day 0 + Due day. For programs shorter than 90 days, tasks with a Due day above {d.FIXED_UNTIL_DAY} "
            f"are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: "
            f"Due day − 90 + Program length. Tasks in section P0 get no date. If Project Day 0 is empty, Due date stays empty.")
count = {m: sum(1 for t in d.TASKS if d.module_of(t[0]) == m) for m in d.MODULES}


def by_module(m):
    return [t for t in ORDERED if d.module_of(t[0]) == m]


def n_sub(ts):
    return sum(len(subtasks.get(t[0], [])) for t in ts)


CHECK_RULE = "Show me the plan and wait for my approval before you change anything."

# ---- 1. Restructure the existing Marketing Hub template into the Task Library ----
MH_IDS = [t[0] for t in by_module("MH")]
CORE_CHANGED = ["0.05", "0.06", "1.02", "1.04", "2.03", "4.07", "4.09", "4.11", "5.11", "6.03"]
changed_lines = "\n".join(f"- {t[0]}: Task = \"{t[2]}\". Depends on = \"{t[8] or '-'}\". Definition of done = \"{t[3]}\""
                          for t in d.TASKS if t[0] in CORE_CHANGED)
mh_renames = ", ".join(f"{i.removeprefix('MH-')} → {i}" for i in MH_IDS)

LIB1 = f"""Restructure the task template in "Client Onboarding" into a task library that covers Marketing, Sales and Service Hub onboarding. Don't create agents, documents or forms. Don't touch the Onboarding Portfolio project in this step.

1. RENAME
Rename the project "Marketing Hub Onboarding (Template)" to "{LIBRARY_PROJECT}", and its Tasks table to "{LIBRARY_TABLE}".

2. MODULE COLUMN
Add a "Module" column (Dropdown: Core, Marketing Hub, Sales Hub, Service Hub) right after Task, and a view "By module" (grouped by Module, then Section).

3. MARKETING HUB MODULE
These {len(MH_IDS)} tasks only apply to Marketing Hub customers. Set Module = Marketing Hub and rename their Task IDs: {mh_renames}. Update every "Depends on" value that points to the old IDs.
Also update these two:
- MH-5.04: Task = "Build 1.4 Subscriber → Engaged (if bought)".
- MH-6.02: Task = "Deliver Marketing Hub training". Definition of done = "Modules T1–T9 as Supered videos + practice in office hours, timed to when each feature ships." Subtasks: {"; ".join(subtasks["MH-6.02"])}.

4. CORE TASKS
Set Module = Core on every other task ({count["Core"]} tasks). Update these to be hub-neutral:
{changed_lines}

{CHECK_RULE} When you're done, confirm: {count["Core"]} Core tasks, {count["MH"]} Marketing Hub tasks, no task without a Module, and no "Depends on" pointing to an ID that no longer exists.
"""


# ---- 2 & 3. Add the Sales and Service Hub modules ----
def add_module_prompt(code):
    ts = by_module(code)
    name = MODULE_NAME[code]
    return f"""Add the {name} module to the "{LIBRARY_TABLE}" table in the "{LIBRARY_PROJECT}" project. Add each task to its section with Module = {name}, Status = Not started, and Task ID, Owner role, Client-facing, Start day, Due day, Repeats, Depends on and Definition of done ("Done when") from its line. Add the "Subtasks" as a checklist under the task. Don't change any existing task.

{sections_for(ts)}

{CHECK_RULE} When you're done, confirm: {len(ts)} new {name} tasks and {n_sub(ts)} subtasks.
"""


LIB2 = add_module_prompt("SH")
LIB3 = add_module_prompt("SV")

# ---- 4. Customers and Customer Task columns ----
LIB4 = f"""Update the "Onboarding Portfolio" project in "Client Onboarding" so a customer's tasks come from the products they bought. Don't create agents, documents or forms.

1. CUSTOMERS TABLE
- Add "Products purchased" (Multi-select: {products}).
- Add "Create tasks" (Checkbox). Ops ticks it to create or add a customer's tasks.
- Replace "Tasks created" with "Tasks created for" (Multi-select, same options as Products purchased). The Task Generator agent fills it with the products whose tasks exist.
- Replace "Marketing Hub tier" with "Hub tiers" (Text, e.g. "Marketing Pro, Sales Enterprise").
- Update the Start date description: "Day 0 = the day the deal reached Start Payment Received, not the kickoff date."

2. CUSTOMER TASK TABLE
Add a "Module" column (Dropdown: Core, Marketing Hub, Sales Hub, Service Hub) right after Task, and a view "By module" (grouped by Customer, then Module).

3. AUTOMATION CLEANUP
- If a task-seeding workflow exists, turn it off. The Onboarding Task Generator agent replaces it.
- Change the Handoff Brief agent's trigger from "Tasks created changes to Yes" to "Tasks created for changes from empty to having a value".

{CHECK_RULE} When you're done, confirm the five Customers changes, the Module column on Customer Task, and the state of the task-seeding workflow and the Handoff Brief trigger.
"""

# ---- Full build from scratch ----
PORTFOLIO_TABLES = f"""Table "Customers", one row per customer. Columns: {customers_cols}.
Views and reports:
{portfolio_views}

Table "Customer Task": every customer's tasks in one table. Same columns as the {LIBRARY_TABLE} table (including the Due date formula, both helper columns, Module and subtasks), plus "Customer" (link to the Customers row) as the second column. Statuses: {statuses}.
Main table: show {visible_ct}. Hide {hidden}.
Views:
{views}
Leave it empty; the Onboarding Task Generator agent fills it.

Table "Request": every customer's requests. Columns: {request_cols}.
Views: "Board by urgency" (columns = Urgency) and "Open requests" (Status not Done or Parked, sorted by Due date).
Use these as the descriptions of the Urgency options:
{request_classes}

Table "Update": drafts the agents write for the Architect. Columns: {update_cols}.
Views:
{update_views}"""

PROMPT = f"""Build a workspace called "Client Onboarding" for RevGravy, a HubSpot consultancy, to run Marketing, Sales and Service Hub onboardings. Build only the projects, tables, columns, views, sections, tasks and subtasks below. Don't create agents (I'll create them in the agent builder), documents or forms.

HOW WE'LL USE IT
- Day 0 is the day the customer's deal reaches "Start Payment Received" in our Sales Pipeline. Programs last 60 to 90 days; the task days below are for a 90-day program.
- Every customer gets the Core tasks once, plus one module per hub they bought (Marketing Hub, Sales Hub, Service Hub).
- All customers share the same tables, and each row links to its Customers row, so agents work across all customers.
{new_customer}

PROJECT 1: "{LIBRARY_PROJECT}"
The master task list. Nobody works in it; customers' tasks are copied from it.

Table "{LIBRARY_TABLE}" with these columns, in this order:
{task_columns}

Statuses, in this order: {statuses}. Every task starts as "Not started".
Main table: show {visible}. Hide {hidden}.
Due date formula: {due_rule} Leave Project Day 0 and Program length empty in the library.
Views:
{library_views}

Create these sections and tasks, in this order. Fill Task ID, Module, Owner role, Client-facing, Start day, Due day, Repeats, Depends on and Definition of done ("Done when") from each line. Add the "Subtasks" as a checklist under the task.

{sections_for(ORDERED)}

PROJECT 2: "Onboarding Portfolio"

{PORTFOLIO_TABLES}

CHECK
When you show me the plan, confirm: 2 projects; the library has {len(d.TASKS)} tasks ({count["Core"]} Core, {count["MH"]} Marketing Hub, {count["SH"]} Sales Hub, {count["SV"]} Service Hub) and {n_sub(d.TASKS)} subtasks; Onboarding Portfolio has 4 tables (Customers, Customer Task, Request, Update). Show me the plan and wait for my approval before you create anything.
"""

# ---- Agents ----
COMMON_RULE = "Only draft, fill fields or flag. Never send anything to a customer and never change a CRM deal."


def agent_prompt(a):
    lines = [f"Name: {a['name']}",
             f"Where: \"Client Onboarding\" workspace, \"Onboarding Portfolio\" project. Tables: Customers, Customer Task, Request, Update. Each row in Customer Task, Request and Update links to its Customers row through the Customer column. The master task list is the \"{LIBRARY_TABLE}\" table in the \"{LIBRARY_PROJECT}\" project.",
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

One prompt per agent for HubSpot Work's agent builder ("What kind of agent do you want to create?"). All schedules are on Bogotá time.

The **Onboarding Task Generator** runs when Ops ticks **Create tasks** on a Customers row. It copies the Core tasks once, plus one module for each product purchased, and records which products are done in **Tasks created for**. Ticking Create tasks again after adding a product (an upsell) adds only the new hub's tasks.

Agents spend HubSpot Credits. Delay Flagger and Portfolio Sync run every day.

""" + "\n".join(agent_blocks)

FILES = [
    ("hubspot-work-library-1-restructure.txt", LIB1, "Turns the Marketing Hub template into the Task Library: Module column, MH- IDs, hub-neutral Core tasks."),
    ("hubspot-work-library-2-sales-hub.txt", LIB2, f"Adds the Sales Hub module ({count['SH']} tasks)."),
    ("hubspot-work-library-3-service-hub.txt", LIB3, f"Adds the Service Hub module ({count['SV']} tasks)."),
    ("hubspot-work-library-4-customers.txt", LIB4, "Adds Products purchased, Create tasks and Tasks created for to Customers, and Module to Customer Task."),
]

GUIDE = f"""# HubSpot Work prompts: client onboarding

All of these are generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

## How tasks get created

The {LIBRARY_TABLE} holds {len(d.TASKS)} tasks: {count["Core"]} Core tasks every customer gets once, plus one module per hub (Marketing Hub {count["MH"]}, Sales Hub {count["SH"]}, Service Hub {count["SV"]}). Ops sets **Products purchased** on the customer's row and ticks **Create tasks**. The Onboarding Task Generator agent copies Core plus the matching modules into the shared Customer Task table, and records them in **Tasks created for**, so ticking it again later only adds new hubs.

All customers share one Customer Task table instead of having a project each, because HubSpot Work agents can't reach into per-customer projects. Filter any view by Customer to see one customer.

## For the workspace you already have, in this order

| Step | File | What it does |
|---|---|---|
""" + "\n".join(f"| {i} | `{f}` | {w} |" for i, (f, _, w) in enumerate(FILES, start=1)) + """
| 5 | `hubspot-work-agent-prompts.md` | Create (or replace) the Onboarding Task Generator agent with prompt #1. The other agents are unchanged. |

Paste steps 1–4 into the workspace chat one at a time, approving each plan. Test with your next real customer before turning the agents on.

## Building from scratch

`hubspot-work-prompt.txt` builds the whole workspace (library with all three hubs, plus the Onboarding Portfolio tables) in a new workspace. Then create the agents.
"""

for f, text, _ in FILES:
    (HERE / f).write_text(text, encoding="utf-8")
(HERE / "hubspot-work-prompt.txt").write_text(PROMPT, encoding="utf-8")
(HERE / "hubspot-work-agent-prompts.md").write_text(AGENTS_MD, encoding="utf-8")
(HERE / "hubspot-work-prompt.md").write_text(GUIDE, encoding="utf-8")
for f, text, _ in FILES:
    print(f"{f}: {len(text):,} characters")
print(f"Full prompt: {len(PROMPT):,} characters, {len(d.TASKS)} tasks, {n_sub(d.TASKS)} subtasks")
print(f"Agent prompts: {len(d.WORK_AGENTS)}, longest {max(len(agent_prompt(a)) for a in d.WORK_AGENTS):,} characters")
