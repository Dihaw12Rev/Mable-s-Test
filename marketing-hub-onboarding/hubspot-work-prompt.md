# HubSpot Work prompts: Marketing Hub Onboarding

All of these are generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

| File | When to use it |
|---|---|
| `hubspot-work-redesign-prompt.txt` | Paste into the chat of the workspace you already built. It switches to shared tables linked to Customers, which is the setup HubSpot Work recommended so agents work across all customers. |
| `hubspot-work-agent-prompts.md` | 8 prompts, one per agent, for the agent builder. Use them after the redesign. |
| `hubspot-work-prompt.txt` | Builds everything from scratch in a new workspace (no agents). |

## Why shared tables

HubSpot Work has no custom project fields, and copying a project doesn't copy its agents' workflows. With one project per customer, every agent would have to be set up again in each copy, and nothing could look across customers. With shared tables, each Customer Task, Request and Update row links to its Customers row, and one set of agents covers everyone.

## Order

1. Paste `hubspot-work-redesign-prompt.txt` in the workspace chat and approve the plan.
2. Make sure the task-seeding workflow exists (or create the Onboarding Task Generator agent from `hubspot-work-agent-prompts.md`).
3. Test it: add a Customers row "Test Co" with Start date today, Program length 60 and yourself as Architect. Expect 74 rows in Customer Task for Test Co, task 4.11 due in 20 days, 8.05 in 60, 9.05 in 240, P0 tasks undated, and Tasks created = Yes.
4. Create the other 7 agents.
5. Delete the Test Co row and its tasks. Share the workspace with Phil and the Architects.

## Redesign prompt

```text
Restructure the "Client Onboarding" workspace the way you recommended: shared tables linked to Customers, so agents work across all customers. Don't create agents; I'll create them in the agent builder. Don't create documents or forms. Don't delete anything that has rows.

1. TEMPLATE PROJECT
Keep "Marketing Hub Onboarding (Template)" and its Tasks table as the master task list. Nobody works in it; new customers' tasks get copied from it.
- Update these tasks:
- 1.01: Task = "Pick the Architect". Owner role = Phil. Definition of done = "Phil checks the Capacity report (active customers per Architect) and picks the Architect."
- 1.02: Task = "Add the customer in HubSpot Work". Owner role = Ops. Definition of done = "Add a Customers row: Customer, Company, Deal, Architect, Program length, Start date, tier, From→To goal, FigJam and Supered links. Check that the Task Generator created the customer's tasks (Tasks created = Yes)."
- Check that the Due date formula follows this rule, and fix it if it doesn't: Due date = Project Day 0 + Due day. For programs shorter than 90 days, tasks with a Due day above 10 are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: Due day − 90 + Program length. Tasks in section P0 get no date. If Project Day 0 is empty, Due date stays empty.
- If the template's Request table has no rows, remove it. Requests now live in the Onboarding Portfolio.

2. ONBOARDING PORTFOLIO PROJECT
Make it hold these four tables.

Table "Customers", one row per customer. Columns: Customer (Text: client name); Company (CRM company); Deal (CRM deal); Architect (HubSpot user); Program length (Number: 60, 75 or 90); Start date (Date: Day 0 = the day the deal reached Start Payment Received, not the kickoff date); Target end date (Date); Marketing Hub tier (Dropdown: Professional, Enterprise); Health (Dropdown: On track, At risk, Off track); Current section (Dropdown: P0–P9, Completed); Next MBR (Date, filled by the Architect when booked); Next due task (Text); Tasks created (Yes/No); From→To goal (Long text); Progress measures (Long text: name, baseline, target); FigJam link (URL); Supered Action Plan link (URL).
Views and reports:
- Capacity: Report: active customers per Architect. Phil uses it to pick the Architect.
- Health board: Columns = Health.
- Ending soon: Target end date in the next 35 days (time for the 'what's next' call).

Table "Customer Task": every customer's tasks in one table. Same columns as the template's Tasks table (including the Due date formula, both helper columns, and subtasks), plus "Customer" (link to the Customers row) as the second column. Statuses: Not started, In progress, Waiting on client, In review, Done, Won't do.
Main table: show Task ID, Customer, Task, Status, Owner role, Assignee, Due date, Client-facing, Repeats, Depends on, Definition of done, Notes. Hide Section, Start day, Due day, Start date, Project Day 0, Program length.
Views:
- Board: Columns = Status. Cards show Customer, Task ID, Task, Assignee, Due date.
- By customer: List grouped by Customer, then Section, sorted by Task ID.
- By section: List grouped by Section (P0 → P9), sorted by Task ID.
- Timeline: Start date → Due date, grouped by Customer.
- Calendar: By Due date.
- My tasks: Assignee = me, Status not Done / Won't do.
- Client to-dos: Owner role = Client POC, Status not Done.
- This week: Due date in the next 7 days, Status not Done.
- Overdue: Due date before today, Status not Done / Won't do.
Leave it empty; the Task Generator fills it for each new customer.

Table "Request": every customer's requests. Columns: Customer (Link to Customers row); Owner (HubSpot user, defaults to the customer's Architect); Request (Text); Urgency (Dropdown: Critical, High, Standard, Not now); Type (Dropdown: Client request, Issue found, Client idea); Status (Dropdown: New, Quoted, In progress, Done, Parked); Price (Number in USD, default 250); Logged on (Date); Due date (Date); Notes (Long text).
Views: "Board by urgency" (columns = Urgency) and "Open requests" (Status not Done or Parked, sorted by Due date).
Use these as the descriptions of the Urgency options:
- Critical: Something live is broken: forms not submitting, emails not sending, a workflow sending the wrong email, tracking down. Reply within 4 business hours; fixed within 1 business day. Price: Free if it's in something we built; otherwise $250.
- High: Needed for a launch or deadline in the next 2 weeks. Reply within 1 business day; done within 5 business days. Price: $250.
- Standard: A small new request with no hard deadline. Reply within 1 business day; done within 10 business days. Price: $250.
- Not now: An idea or a bigger project for later. Logged and reviewed at MBRs and the 'what's next' call. Price: Quoted when scoped.

Table "Update": drafts the agents write for the Architect. Columns: Customer (Link to Customers row); Type (Dropdown: Handoff brief, Weekly update, What's next options, KPI snapshot, Delay flag); Period (Date: week of, or month); Draft (Long text); Status (Dropdown: Draft (an agent wrote it), Reviewed (the Architect checked it), Sent (the Architect sent it to the customer)); Notes (Long text).
Views:
- To review: Status = Draft, grouped by Customer.
- By customer: Grouped by Customer, newest first.

3. HOW WE'LL USE IT
1. Add a row to Customers: Customer, Company, Deal, Architect, Program length, Start date, tier, From→To goal, FigJam and Supered links.
2. The Task Generator (a workflow) copies the template tasks into Customer Task for that customer, fills the dates, assigns the Architect and sets Tasks created = Yes.
3. To work on one customer, filter any view by Customer. 'My tasks' shows an Architect's work across all their customers.
4. Share the workspace with Phil and the Architects (it's private by default).

Show me the plan and wait for my approval before you change anything. When you're done, confirm: 4 tables in Onboarding Portfolio (Customers, Customer Task, Request, Update), 9 views on Customer Task, 0 rows in Customer Task, and tasks 1.01 and 1.02 updated in the template.
```
