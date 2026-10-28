# HubSpot Work build prompt — Marketing Hub Onboarding

HubSpot Work builds a workspace from a plain-language description: it drafts a plan, waits for approval, and then creates tables, documents, forms and agents. Paste the prompt below into HubSpot Work when the team is ready to build. Review the plan it proposes before approving anything.

The prompt is written to match `Marketing_Hub_Onboarding_Process.xlsx`. If you change the sheet, update the prompt too.

---

## Prompt (copy everything inside the box)

```text
Build a workspace called "Client Onboarding" with one project called "Marketing Hub Onboarding" for RevGravy, a HubSpot consultancy. Each customer who buys a Marketing Hub onboarding program goes through a 90-day program. Day 0 is when the deal reaches the "Start Payment Received" stage in our Sales Pipeline.

Roles: Phil (strategy lead, owns the sale and the handoff), Architect (assigned delivery lead, owns the customer's onboarding), Ops (admin), AI (drafts only, a human always reviews), Client POC (customer's main contact).

Phases, with start and end day:
P1 Close & welcome (0–3), P2 Access & intake (1–7), P3 Kickoff (5–10), P4 Foundations / technical setup (7–30), P5 Build & launch (21–75), P6 Training & adoption (14–85), P7 Run cadence: office hours, Friday weekly updates, monthly business reviews (7–90), P8 What's next (60–90), P9 Post-program: 6 months of free KPI monitoring and continuation offers (90–365).

Create these tables:
1. Onboarding Tracker — one row per customer. Columns: Company (CRM company lookup), Deal (CRM deal lookup), Architect (user), Phase (dropdown P1–P9 with the names above), Health (On track / At risk / Off track), Start date, Kickoff date, Next MBR date, Planned end date (Start date + 90 days), From→To goal (text), Success metrics (text), Risks & blockers (text), FigJam link, Supered Action Plan link, Office hours link, Access status (Not started / Partial / Complete), Intake status (Not sent / Sent / Submitted), Last weekly update sent (date).
2. Task Template Library — the standard task list. Columns: Task ID, Phase, Task, Definition of done, Owner role, Client-facing (yes/no), Start day offset, Due day offset, Depends on, Where it lives in HubSpot. I will import the rows from our spreadsheet.
3. Customer Tasks — tasks generated per customer from the template. Columns: Customer (link to Onboarding Tracker), Task (link to Task Template Library), Owner (user), Due date (customer Start date + Due day offset), Status (To do / In progress / Waiting on client / Done / Won't do), Notes.
4. Tech Setup Checklist — per customer. Columns: Customer, Area, Item, Tier (Starter / Pro / Enterprise), Status, Notes.
5. Intake Responses — fed by the Client Intake Form.
6. Issues & Not-Now Ideas — Customer, Type (Issue found / Client idea / Out-of-scope request), Description, Date found, Urgency, Suggested offer, Status (Logged / Quoted / Sold / Parked).
7. Weekly Update Log — Customer, Week of, Draft (link to document), Sent (yes/no), Sent date.
8. Training Tracker — Customer, Module (T1–T9), Audience, Due, Status.

Create these forms:
- Client Intake Form → Intake Responses. Sections: Contacts, Goals, Audience, Marketing today, Content approval, Tech, Compliance, Brand (file upload), Access checklist. Questions are listed on the "Intake Form" tab of our spreadsheet; I will paste them in.
- Sales → Architect Handoff Form → Onboarding Tracker. Fields: Company, Deal, From→To goal, products bought, progress measures, POC, supporters, AI terms confirmed, escalation path, FigJam link, notes.
- New Request Form → Issues & Not-Now Ideas, with urgency class.

Create these documents:
- Onboarding Playbook (one section per phase: goal, what the client sees, exit criteria, tasks).
- Kickoff Agenda (15 minutes: intros, confirm goal and plan, missing items, office hours, weekly updates, MBRs, request process).
- Weekly Update Template (1. what we did and which strategic issue it moves, 2. KPIs vs baseline, 3. issues found that are not in scope, 4. next week, 5. your to-dos).
- MBR Template (progress vs benchmark, KPI trend, issues and opportunities).
- "What's Next" Call Script (results so far, the next phase as an A/B choice, Architect joins).
- Welcome Email Copy (email #1 Day 0 and email #2 Day 2).

Create these agents, all drafting only and never sending to customers on their own:
- Handoff Brief agent: when a new row is added to Onboarding Tracker, read the associated deal's history, notes and meetings and write a one-page handoff brief for the Architect.
- Task Generator agent: when a new row is added to Onboarding Tracker, create Customer Tasks from the Task Template Library with due dates from the customer's Start date.
- Weekly Update Drafter: every Thursday, for each active customer, draft the weekly update from Customer Tasks completed this week, Issues & Not-Now Ideas, and the KPI notes, using the Weekly Update Template. Add a row to Weekly Update Log for the Architect to review.
- Delay Flagger: every weekday, flag Customer Tasks past due or "Waiting on client" for more than 3 days, and set Health to At risk when 3 or more tasks are overdue. Notify the Architect and Phil.
- What's Next Prep agent: on day 55 for each customer, summarize results, issues found and not-now ideas into two next-phase options for Phil.

Show me the plan before building.
```

---

## Before you paste it

1. A Super Admin enrolls the portal in the HubSpot Work public beta and turns on generative AI. Users need a Core, Sales or Service seat.
2. Agents spend HubSpot Credits. Check the credit balance before turning on the scheduled agents (the Weekly Update Drafter and the Delay Flagger run most often).
3. Paste the task rows from the **Task Template** tab and the questions from the **Intake Form** tab after the tables and forms exist.
4. Test with one internal "dummy" customer before using it with a real one.
