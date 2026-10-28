"""Build the exact HubSpot Work prompt from process_data.py.

Writes two paste-ready prompts (prompt 1 builds the workspace, prompt 2 loads
the rows into it) and hubspot-work-prompt.md (both prompts plus how to use them).

Run:  python3 build_prompt.py
"""
from pathlib import Path

import process_data as d

HERE = Path(__file__).parent
PHASE_NAME = {p["id"]: p["name"] for p in d.PHASES}

phases = "\n".join(f"- {p['id']} {p['name']} (day {p['start']} to {p['end']}): {p['goal']}"
                   for p in d.PHASES if p["id"] != "P0")
roles = "\n".join(f"- {r}: {desc}" for r, desc in d.ROLES.items())

tasks = "\n".join(
    f"{tid} | {ph} {PHASE_NAME[ph]} | {task} | Owner: {owner} | Client-facing: {cf} | Start day: {s} | "
    f"Due day: {e} | Depends on: {dep or '-'} | Lives in: {where} | Definition of done: {det}"
    for tid, ph, task, det, owner, cf, s, e, dep, where, auto in d.TASKS if ph != "P0")

intake = "\n".join(
    f"{i}. [{sec}] {q} | Field type: {ft} | Required: {req} | Pre-filled from the deal: {pre}"
    for i, (sec, q, ft, req, pre, why, maps) in enumerate(d.INTAKE, start=1))

tech = "\n".join(f"{area} | {item} | Tier: {tier} | Task: {tid} | Owner: {owner} | {det}"
                 for area, item, det, tier, tid, owner in d.TECH_SETUP)

training = "\n".join(f"{m} | Audience: {a} | Format: {f} | When: {w} | Length: {l} | {c}"
                     for m, a, c, f, w, l in d.TRAINING)

handoff = "\n".join(f"- {task}: {det}" for tid, ph, task, det, *_ in d.TASKS if ph == "P0")

PROMPT = f"""Build a workspace called "Client Onboarding" with one project inside it called "Marketing Hub Onboarding".

CONTEXT
RevGravy is a HubSpot consultancy. When a customer buys our Marketing Hub onboarding, they go through a program that targets 90 days. Day 0 is the day their deal reaches the "Start Payment Received" stage of our Sales Pipeline. This project is where our team runs every customer's onboarding. It is internal only; customers never see it. Customer-facing material lives in Supered.

ROLES
{roles}

PHASES
{phases}

STEP 1. CREATE THESE TABLES

Table 1: "Onboarding Tracker" (one row per customer)
Columns: Company (CRM company lookup), Deal (CRM deal lookup), Main contact (CRM contact lookup), Architect (HubSpot user), Phase (dropdown: P1 Close & welcome, P2 Access & intake, P3 Kickoff, P4 Foundations, P5 Build & launch, P6 Training & adoption, P7 Run cadence, P8 What's next, P9 Post-program, Completed, Paused, Cancelled), Health (dropdown: On track, At risk, Off track), Start date (date), Kickoff date (date), Next MBR date (date), Target end date (date, Start date + 90 days), From-to goal (long text), Success metrics (long text), Risks and blockers (long text), HubSpot tier (dropdown: Starter, Professional, Enterprise), FigJam link (URL), Supered Action Plan link (URL), Office hours booking link (URL), Access status (dropdown: Not started, Partial, Complete), Intake status (dropdown: Not sent, Sent, Submitted), Last weekly update sent (date).

Table 2: "Task Template Library" (the standard task list; I will give you the rows in my next message)
Columns: Task ID (text), Phase (dropdown P1 to P9), Task (text), Owner role (dropdown: Phil, Architect, Ops, AI, Automation, Client POC, Client team), Client-facing (Yes/No), Start day (number), Due day (number), Depends on (text), Lives in (text), Definition of done (long text).

Table 3: "Customer Tasks" (generated per customer from the template)
Columns: Customer (link to Onboarding Tracker), Task ID (link to Task Template Library), Task (text), Owner (HubSpot user), Due date (date), Status (dropdown: To do, In progress, Waiting on client, Done, Won't do), Notes (long text).

Table 4: "Tech Setup Library" (the standard Marketing Hub setup checklist; I will give you the rows in my next message)
Columns: Area (dropdown), Item (text), Tier (dropdown: S, P, E where S = all tiers, P = Professional and up, E = Enterprise only), Task ID (text), Owner (text), Details (long text).

Table 5: "Customer Tech Setup" (per customer)
Columns: Customer (link to Onboarding Tracker), Item (link to Tech Setup Library), Status (dropdown: Not started, In progress, Done, Not applicable), Notes (long text).

Table 6: "Intake Responses" (filled by the Client Intake Form)
One column per intake question (I will give you the questions in my next message), plus Customer (link to Onboarding Tracker) and Submitted date.

Table 7: "Issues and Not-Now Ideas"
Columns: Customer (link to Onboarding Tracker), Type (dropdown: Issue found, Client idea, Out-of-scope request), Description (long text), Date found (date), Urgency (dropdown: Urgent, This week, This month, Not now), Suggested offer (text), Price (number, default 250), Status (dropdown: Logged, Quoted, Sold, Parked).

Table 8: "Weekly Update Log"
Columns: Customer (link to Onboarding Tracker), Week of (date), Draft (link to a document), Reviewed by Architect (Yes/No), Sent (Yes/No), Sent date (date).

Table 9: "Training Tracker"
Columns: Customer (link to Onboarding Tracker), Module (dropdown T1 to T9), Audience (text), Due date (date), Status (dropdown: Not started, Shared, Completed).

STEP 2. CREATE THESE FORMS

Form 1: "Sales to Architect Handoff" (internal, creates a row in Onboarding Tracker)
Fields: Company, Deal, Main contact, Supporters, From-to goal, Products bought, Progress measures, HubSpot tier, FigJam link, AI terms confirmed (Yes/No), Escalation path, Notes for the Architect.
Before this form is submitted, these pre-sale items must be true:
{handoff}

Form 2: "Client Intake Form" (sent to the customer's main contact, fills Intake Responses)
Create the form with a placeholder question; I will give you the questions in my next message. Group them by their section, in that order. Questions marked "Pre-filled from the deal: Yes" should show the answer we already have and ask the customer to confirm it.

Form 3: "New Request" (internal, creates a row in Issues and Not-Now Ideas)
Fields: Customer, Type, Description, Urgency.

STEP 3. CREATE THESE DOCUMENTS

1. "Onboarding Playbook": one section per phase (P1 to P9) with the goal, what the client sees, the exit criteria, and the tasks for that phase from Task Template Library.
2. "Kickoff Agenda (15 minutes)": introductions of the Architect and team; confirm the from-to goal and the 90-day plan; walk through missing items and who owns them; explain office hours, Friday weekly updates and monthly business reviews; explain how to request work and the urgency classes; book MBR #1 (about day 30), MBR #2 (about day 60) and the final results review (about day 85).
3. "Weekly Update Template": five sections. 1) What we did this week and which strategic issue it moves. 2) KPIs compared with the baseline. 3) Issues we found that are not in scope. 4) What we will do next week. 5) Your to-dos.
4. "MBR Template": progress against the baseline for each progress measure, KPI trend, issues and opportunities found, decisions needed.
5. "What's Next Call Script": results so far, the long-term vision for the customer, the next phase as two options (A and B), and the post-program offers: 6 months of free KPI monitoring, paid team support, paid help building internal capacity, and one initiative a month.
6. "Welcome Emails": Email 1 on day 0 from Phil (welcome, Supered Action Plan link, kickoff booking link, first to-dos: grant HubSpot access and complete the intake form). Email 2 on day 2 (how we work: office hours, weekly updates, how to request work and urgency classes, escalation path, how we use AI).

STEP 4. CREATE THESE AGENTS
Every agent only drafts or flags. None of them sends anything to a customer.

Agent 1: "Handoff Brief". Trigger: a new row in Onboarding Tracker. Read the linked deal's history, notes, meetings and emails, and write a one-page brief for the Architect: who the customer is, the from-to goal, what they bought, the progress measures, people involved, risks, and open questions. Save it as a document linked to the row and notify the Architect.

Agent 2: "Task Generator". Trigger: a new row in Onboarding Tracker. Create one Customer Tasks row for every row in Task Template Library. Due date = the customer's Start date + Due day. Owner = the customer's Architect when Owner role is Architect, and leave it empty for other roles so a person can assign it. Also create one Customer Tech Setup row for every Tech Setup Library item that applies to the customer's HubSpot tier (S items for every customer, P items for Professional and Enterprise, E items for Enterprise only), and one Training Tracker row per training module.

Agent 3: "Weekly Update Drafter". Schedule: every Thursday. For each Onboarding Tracker row whose Phase is P2 to P8, draft that week's update with the Weekly Update Template. Use the Customer Tasks marked Done this week, the Issues and Not-Now Ideas logged this week, and the customer's KPIs. Add a row to Weekly Update Log with Reviewed by Architect = No and notify the Architect.

Agent 4: "Delay Flagger". Schedule: every weekday morning. Flag Customer Tasks that are past due, or that have been "Waiting on client" for more than 3 days. If a customer has 3 or more overdue tasks, set Health to At risk. Notify the Architect, and notify Phil when Health changes to At risk or Off track.

Agent 5: "What's Next Prep". Trigger: 55 days after a customer's Start date. Summarize the results so far, the issues found and the not-now ideas into two next-phase options (A and B) for Phil. Save it as a document and create a Customer Tasks row "Prep the what's next call", owned by Phil and due on day 60.

__SPLIT__Load these rows into the tables and form you just built in the "Marketing Hub Onboarding" project. Add every row exactly as written. Do not change, merge or skip any.

Task Template Library rows (one per line, columns separated by |):
{tasks}

Client Intake Form questions (one per line):
{intake}

Tech Setup Library rows (one per line, columns separated by |):
{tech}

Training modules (one per line). Use them as the Module dropdown options in Training Tracker, and have the Task Generator agent create one Training Tracker row per module for each new customer:
{training}

When you're done, tell me how many rows each table has. Expect __COUNTS__.
"""

counts = (f"{sum(1 for t in d.TASKS if t[1] != 'P0')} Task Template Library rows, {len(d.INTAKE)} intake questions, "
          f"{len(d.TECH_SETUP)} Tech Setup Library rows and {len(d.TRAINING)} training modules")
BUILD, LOAD = PROMPT.split("__SPLIT__")
BUILD = BUILD.rstrip() + """

STEP 5. BEFORE YOU BUILD
Show me the full plan (tables, forms, documents, agents) and wait for my approval before you create anything. After the build, I will send a second message with the rows to load.
"""
LOAD = LOAD.replace("__COUNTS__", counts)

GUIDE = """# HubSpot Work prompt: Marketing Hub Onboarding

There are two prompts, pasted as two messages in the same HubSpot Work chat:

- `hubspot-work-prompt-1-build.txt` builds the workspace: tables, forms, documents and agents.
- `hubspot-work-prompt-2-load-rows.txt` loads the task template, intake questions, tech setup checklist and training modules.

Both are generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

## How to use it

1. A Super Admin enrolls the portal in the HubSpot Work public beta and turns on generative AI. Users need a Core, Sales or Service seat.
2. Open HubSpot Work and start a new workspace from a blank prompt.
3. Paste all of Prompt 1. HubSpot Work shows a plan first: check it against Steps 1–4, then approve.
4. When the build finishes, paste all of Prompt 2 in the same chat.
5. Check the row counts it reports against the last line of Prompt 2.
6. Test with one internal dummy customer before using it with a real one.

If Prompt 2 is still too long, send it in pieces (tasks, then intake questions, then tech setup and training), starting each piece with its first line.

Agents spend HubSpot Credits. Check the credit balance before turning on the scheduled agents; the Weekly Update Drafter and the Delay Flagger run most often.

## Prompt 1: build the workspace

```text
""" + BUILD + """```

## Prompt 2: load the rows

```text
""" + LOAD + """```
"""

(HERE / "hubspot-work-prompt-1-build.txt").write_text(BUILD, encoding="utf-8")
(HERE / "hubspot-work-prompt-2-load-rows.txt").write_text(LOAD, encoding="utf-8")
(HERE / "hubspot-work-prompt.md").write_text(GUIDE, encoding="utf-8")
for name, text in (("Prompt 1", BUILD), ("Prompt 2", LOAD)):
    print(f"{name}: {len(text):,} characters")
