# HubSpot Work prompt: Marketing Hub Onboarding

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
Build a workspace called "Client Onboarding" with one project inside it called "Marketing Hub Onboarding".

CONTEXT
RevGravy is a HubSpot consultancy. When a customer buys our Marketing Hub onboarding, they go through a program that targets 90 days. Day 0 is the day their deal reaches the "Start Payment Received" stage of our Sales Pipeline. This project is where our team runs every customer's onboarding. It is internal only; customers never see it. Customer-facing material lives in Supered.

ROLES
- Phil: Strategy lead. Owns the sale, the Architect handoff, MBR strategy and the 'what's next' conversation.
- Architect: Assigned delivery lead. Owns the onboarding record, the build, weekly updates and office hours.
- Ops: RevGravy operations/admin. Owns templates, Supered setup, data hygiene of the process itself.
- AI: AI agent drafts (handoff brief, agendas, weekly updates). A human always reviews before anything is sent.
- Automation: HubSpot workflow, no human action needed.
- Client POC: Main point of contact at the customer. Owns approvals, access and client to-dos.
- Client team: Supporters / end users at the customer who get trained and use the portal.

PHASES
- P1 Close & welcome (day 0 to 3): Customer feels the handoff instantly; the Architect is assigned and briefed within 72 hours.
- P2 Access & intake (day 1 to 7): Get every access and input we need in week 1, and replace Trello with HubSpot + Supered.
- P3 Kickoff (day 5 to 10): 15 minutes that confirm the plan, close gaps and set the operating rhythm.
- P4 Foundations (tech setup) (day 7 to 30): Marketing Hub is set up correctly: tracking, domains, email auth, data model, imports, baseline reporting.
- P5 Build & launch (day 21 to 75): Ship the tactical outcomes the customer bought, each tied to a progress measure.
- P6 Training & adoption (day 14 to 85): The customer's team can run what we built without us.
- P7 Run cadence (day 7 to 90): A predictable rhythm: office hours, Friday updates, monthly business reviews, managed requests.
- P8 What's next (day 60 to 90): Customer sees the long-term vision and chooses the next phase before the program ends.
- P9 Post-program (day 90 to 365): Keep the relationship for 6–12 more months.

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
- Research brief from company URL: Website URL on the deal; AI research brief attached as a note before the Fit call.
- FigJam canvas created after Fit call: Canvas covers strategic motivation, tactical outcomes, progress measures and fee range. Link saved to the deal and later copied to the onboarding record.
- Strategic motivation captured ('From X to Y'): One sentence: from where they are today to where they want to be. This is the north star the weekly updates tie back to.
- Tech stack & team capacity survey completed: Client gives HubSpot access and completes the survey (form or AI chat): tools beyond HubSpot, internal processes and cadences, current KPIs and progress measures.
- Products and quote on the deal: Pricing calculator used; line items added; quote created.
- Progress measures defined: Each tactical outcome has a progress measure (Factory) with a baseline if known.
- POC and supporters identified: Contacts associated to the deal with association labels (POC, Supporter, Billing, Decision maker). POC enrolled in the weekly email.
- Agreement signed: Includes AI terms, escalation path, how progress is measured, main POC and supporters, strategic job → tactical outcomes → progress measures, and new-request handling with urgency classification ($250).
- Definition of Ready gate: Deal cannot move to 'Start Payment Received' unless the required handoff properties are filled.

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

STEP 5. BEFORE YOU BUILD
Show me the full plan (tables, forms, documents, agents) and wait for my approval before you create anything. After the build, I will send a second message with the rows to load.
```

## Prompt 2: load the rows

```text
Load these rows into the tables and form you just built in the "Marketing Hub Onboarding" project. Add every row exactly as written. Do not change, merge or skip any.

Task Template Library rows (one per line, columns separated by |):
1.01 | P1 Close & welcome | Create onboarding record | Owner: Automation | Client-facing: No | Start day: 0 | Due day: 0 | Depends on: 0.09 | Lives in: Onboarding record + workflow | Definition of done: Deal reaches 'Start Payment Received' → onboarding record created from the Marketing Hub template and associated to deal, company and contacts; deal context copied over.
1.02 | P1 Close & welcome | Assign Architect | Owner: Phil | Client-facing: No | Start day: 0 | Due day: 1 | Depends on: 1.01 | Lives in: Onboarding record owner | Definition of done: Phil picks the Architect (or rotation by capacity). Architect becomes owner of the onboarding record and company.
1.03 | P1 Close & welcome | Notify team with handoff brief | Owner: AI | Client-facing: No | Start day: 0 | Due day: 1 | Depends on: 1.02 | Lives in: Slack + Note on onboarding record | Definition of done: Slack + HubSpot notification to the delivery team. AI drafts the brief from deal history, FigJam and survey.
1.04 | P1 Close & welcome | Welcome email #1: welcome + Action Plan | Owner: Automation | Client-facing: Yes | Start day: 0 | Due day: 0 | Depends on: 1.01 | Lives in: Marketing email / sequence | Definition of done: Sent from Phil. Links to the Supered Action Plan: expectations, next steps, how the partnership works, agreement, client to-dos, kickoff booking link.
1.05 | P1 Close & welcome | Build Supered Action Plan from template | Owner: Ops | Client-facing: Yes | Start day: 0 | Due day: 1 | Depends on: 1.01 | Lives in: Supered | Definition of done: Duplicate the Marketing Hub Action Plan template. Add the agreement, FigJam, client to-dos and access checklist.
1.06 | P1 Close & welcome | Instantiate Delivery Template | Owner: Architect | Client-facing: No | Start day: 1 | Due day: 3 | Depends on: 1.02 | Lives in: Factory records (Projects object) | Definition of done: Create one Factory (progress measure) record per tactical outcome bought, with benchmark, schedule and client to-dos.
1.07 | P1 Close & welcome | Set internal progress measures | Owner: Ops | Client-facing: No | Start day: 0 | Due day: 1 | Depends on: 1.01 | Lives in: Onboarding record properties | Definition of done: Planned end date, hours budget, health = On track, next MBR date.
1.08 | P1 Close & welcome | Phil ↔ Architect 1:1 handoff (30 min) | Owner: Phil | Client-facing: No | Start day: 1 | Due day: 3 | Depends on: 1.02 | Lives in: Meeting on onboarding record | Definition of done: Walk through FigJam, customer context, products chosen, the goal, outcomes, how success is measured (KPIs), the Delivery Template and schedule.
1.09 | P1 Close & welcome | Office hours booking link ready | Owner: Architect | Client-facing: Yes | Start day: 1 | Due day: 2 | Depends on: 1.02 | Lives in: HubSpot Meetings | Definition of done: Architect's HubSpot Meetings link (office-hours type) added to the Supered plan.
1.10 | P1 Close & welcome | Welcome email #2: how we work | Owner: Automation | Client-facing: Yes | Start day: 2 | Due day: 2 | Depends on: 1.04 | Lives in: Marketing email / sequence | Definition of done: Office hours, weekly updates, how to request work and the urgency classes, escalation path, how we use AI.
1.11 | P1 Close & welcome | Kickoff booked | Owner: Client POC | Client-facing: Yes | Start day: 0 | Due day: 5 | Depends on: 1.04 | Lives in: Meeting | Definition of done: Client books the 15-minute kickoff via the link in welcome email #1. Reminder at Day 3 if not booked.
2.01 | P2 Access & intake | HubSpot access granted | Owner: Client POC | Client-facing: Yes | Start day: 1 | Due day: 3 | Depends on: 1.04 | Lives in: Client to-do in Supered | Definition of done: Partner access or a Super Admin user for the Architect. Confirm the hub tiers (Marketing Starter / Pro / Enterprise).
2.02 | P2 Access & intake | Onboarding intake form submitted | Owner: Client POC | Client-facing: Yes | Start day: 1 | Due day: 5 | Depends on: 1.04 | Lives in: Form → onboarding record | Definition of done: Short form that asks only what pre-sale didn't capture (see Intake Form tab).
2.03 | P2 Access & intake | Access to connected systems | Owner: Client POC | Client-facing: Yes | Start day: 1 | Due day: 7 | Depends on: 2.02 | Lives in: Access checklist (intake) | Definition of done: DNS/IT contact, website CMS, GA4/GTM, ad accounts, social accounts, any CRM or email tool we migrate from.
2.04 | P2 Access & intake | Brand & content assets shared | Owner: Client POC | Client-facing: Yes | Start day: 1 | Due day: 7 | Depends on: 2.02 | Lives in: File upload on intake form | Definition of done: Brand guide, logos, fonts, colors, existing email templates, key content, lists to import.
2.05 | P2 Access & intake | Supered announcement to POC | Owner: Architect | Client-facing: Yes | Start day: 2 | Due day: 3 | Depends on: 1.05 | Lives in: Supered | Definition of done: Short video: how Supered works (Bases, announcements, documentation) and where updates will show up.
2.06 | P2 Access & intake | Portal audit (current state) | Owner: Architect | Client-facing: No | Start day: 3 | Due day: 7 | Depends on: 2.01 | Lives in: Note on onboarding record | Definition of done: Data health, email health, existing assets, tracking code, workflows, properties. Output: 1-page audit summary for kickoff.
2.07 | P2 Access & intake | Baseline KPI snapshot | Owner: Architect | Client-facing: No | Start day: 5 | Due day: 7 | Depends on: 2.06 | Lives in: Factory records: baseline | Definition of done: Record the 'before' numbers for each progress measure (sessions, leads, MQLs, meetings, etc.).
2.08 | P2 Access & intake | No Trello | Owner: Architect | Client-facing: No | Start day: 1 | Due day: 1 | Depends on: - | Lives in: Policy | Definition of done: All delivery work lives in HubSpot (tasks on the onboarding record) and client-facing docs in Supered. Architect owns this.
3.01 | P3 Kickoff | Kickoff agenda drafted | Owner: AI | Client-facing: No | Start day: 5 | Due day: 7 | Depends on: 2.02, 2.06 | Lives in: Doc / note | Definition of done: AI drafts from intake + audit: plan summary, missing items, decisions needed. Architect edits.
3.02 | P3 Kickoff | Kickoff session (15 min) | Owner: Architect | Client-facing: Yes | Start day: 5 | Due day: 10 | Depends on: 3.01 | Lives in: Meeting | Definition of done: Architect & team intro; confirm goal and 90-day plan; walk through missing items; explain office hours, weekly updates, MBRs and request process.
3.03 | P3 Kickoff | Book MBRs and the 'what's next' call | Owner: Architect | Client-facing: Yes | Start day: 5 | Due day: 10 | Depends on: 3.02 | Lives in: Meetings | Definition of done: MBR #1 ≈ Day 30, MBR #2 ≈ Day 60 (includes what's next), final results review ≈ Day 85.
3.04 | P3 Kickoff | Kickoff recap within 24h | Owner: Architect | Client-facing: Yes | Start day: 6 | Due day: 11 | Depends on: 3.02 | Lives in: Email + Supered | Definition of done: AI drafts the recap; Architect sends. Supered plan updated with confirmed schedule and client to-dos.
3.05 | P3 Kickoff | Move onboarding to Foundations | Owner: Architect | Client-facing: No | Start day: 6 | Due day: 11 | Depends on: 3.02 | Lives in: Onboarding pipeline stage | Definition of done: Stage = Foundations, health set.
4.01 | P4 Foundations (tech setup) | Account settings, users & permissions | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 12 | Depends on: 2.01 | Lives in: Tech Setup tab | Definition of done: Users, teams, permission sets, 2FA, account defaults, brands/business units if relevant.
4.02 | P4 Foundations (tech setup) | Tracking code & consent | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 14 | Depends on: 2.03 | Lives in: Tech Setup tab | Definition of done: Tracking code on every site domain, internal IPs excluded, cookie consent banner configured.
4.03 | P4 Foundations (tech setup) | Domains & email authentication | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 18 | Depends on: 2.03 | Lives in: Tech Setup tab | Definition of done: Connect landing page / blog domains; authenticate the email sending domain (SPF, DKIM, DMARC). Needs client DNS contact.
4.04 | P4 Foundations (tech setup) | Email foundations | Owner: Architect | Client-facing: No | Start day: 10 | Due day: 18 | Depends on: 2.04 | Lives in: Tech Setup tab | Definition of done: Subscription types, footer and office address, brand kit, email templates, default sender.
4.05 | P4 Foundations (tech setup) | Data model | Owner: Architect | Client-facing: No | Start day: 10 | Due day: 21 | Depends on: 2.06 | Lives in: Tech Setup tab | Definition of done: Property audit, custom properties, lifecycle stage definitions, lead status, marketing-contact rules.
4.06 | P4 Foundations (tech setup) | Data import & cleanup | Owner: Architect | Client-facing: No | Start day: 14 | Due day: 25 | Depends on: 4.05 | Lives in: Tech Setup tab | Definition of done: Import contacts/companies, dedupe, associations, set marketing contacts.
4.07 | P4 Foundations (tech setup) | Integrations | Owner: Architect | Client-facing: No | Start day: 14 | Due day: 28 | Depends on: 2.03 | Lives in: Tech Setup tab | Definition of done: Website forms, GA4, ad accounts, social, webinar/Zoom, Slack, CRM sync if the CRM isn't HubSpot.
4.08 | P4 Foundations (tech setup) | Baseline progress dashboard | Owner: Architect | Client-facing: Yes | Start day: 18 | Due day: 28 | Depends on: 2.07 | Lives in: HubSpot dashboard | Definition of done: Dashboard with one report per progress measure, so weekly updates can show KPIs.
4.09 | P4 Foundations (tech setup) | Foundation QA | Owner: Architect | Client-facing: No | Start day: 25 | Due day: 30 | Depends on: 4.02, 4.03, 4.04 | Lives in: QA checklist | Definition of done: Test tracking, a test email (deliverability + rendering), test form submission end to end.
4.10 | P4 Foundations (tech setup) | Supered announcement: foundations done | Owner: Architect | Client-facing: Yes | Start day: 28 | Due day: 30 | Depends on: 4.09 | Lives in: Supered | Definition of done: Short video: what changed for you and why it matters.
5.01 | P5 Build & launch | Lead capture | Owner: Architect | Client-facing: No | Start day: 21 | Due day: 40 | Depends on: 4.09 | Lives in: Factory: Visitor → Lead | Definition of done: Forms, CTAs/pop-ups, landing pages, thank-you pages, meetings link.
5.02 | P5 Build & launch | Segmentation | Owner: Architect | Client-facing: No | Start day: 25 | Due day: 40 | Depends on: 4.06 | Lives in: Factory | Definition of done: Segments by persona, lifecycle and engagement; suppression lists.
5.03 | P5 Build & launch | Lead nurture | Owner: Architect | Client-facing: Yes | Start day: 30 | Due day: 55 | Depends on: 5.01, 5.02 | Lives in: Factory: Lead → MQL | Definition of done: Nurture workflows and emails per persona/offer. Client approves copy.
5.04 | P5 Build & launch | Lifecycle automation & MQL handoff | Owner: Architect | Client-facing: Yes | Start day: 35 | Due day: 60 | Depends on: 4.05 | Lives in: Factory: MQL → Meeting | Definition of done: Lead scoring (Pro+), MQL criteria, owner assignment, sales notifications, follow-up SLA.
5.05 | P5 Build & launch | First campaign live | Owner: Architect | Client-facing: Yes | Start day: 40 | Due day: 65 | Depends on: 5.01, 5.03 | Lives in: Factory | Definition of done: Campaign object, UTMs, assets associated, launched with the client.
5.06 | P5 Build & launch | Ads & social | Owner: Architect | Client-facing: No | Start day: 30 | Due day: 60 | Depends on: 4.07 | Lives in: Factory | Definition of done: Connect ad accounts, conversion events, audiences (Pro+), social publishing.
5.07 | P5 Build & launch | Performance reporting | Owner: Architect | Client-facing: Yes | Start day: 45 | Due day: 70 | Depends on: 4.08 | Lives in: HubSpot dashboard | Definition of done: Marketing performance dashboard, funnel by progress measure, attribution (Pro/Ent).
5.08 | P5 Build & launch | AI / Breeze configuration | Owner: Architect | Client-facing: No | Start day: 45 | Due day: 70 | Depends on: 4.04 | Lives in: Tech Setup tab | Definition of done: Brand voice, content tools and agents, only within the AI terms in the agreement.
5.09 | P5 Build & launch | UAT & go-live per Factory | Owner: Client POC | Client-facing: Yes | Start day: 35 | Due day: 75 | Depends on: 5.01–5.08 | Lives in: Factory record stage | Definition of done: Client reviews and approves each delivery; Factory moves to Done.
5.10 | P5 Build & launch | Supered video per delivery | Owner: Architect | Client-facing: Yes | Start day: 35 | Due day: 75 | Depends on: 5.09 | Lives in: Supered | Definition of done: What was built, how to use it, why it matters.
5.11 | P5 Build & launch | Log issues found & out of scope | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 90 | Depends on: - | Lives in: Tickets | Definition of done: Anything uncovered that's not in scope becomes a ticket ('sell the problem') or a 'not now' item.
6.01 | P6 Training & adoption | Confirm training plan | Owner: Architect | Client-facing: Yes | Start day: 10 | Due day: 14 | Depends on: 2.02 | Lives in: Training tab | Definition of done: Who needs which modules (from intake). See Training tab.
6.02 | P6 Training & adoption | Deliver training modules | Owner: Architect | Client-facing: Yes | Start day: 14 | Due day: 85 | Depends on: 6.01 | Lives in: Supered + office hours | Definition of done: Supered videos + live practice in office hours, timed to when each feature ships.
6.03 | P6 Training & adoption | Adoption check #1 | Owner: Architect | Client-facing: No | Start day: 45 | Due day: 45 | Depends on: 6.02 | Lives in: Onboarding record | Definition of done: Logins, emails sent, workflows active, dashboards viewed. Flag low adoption in the weekly update.
6.04 | P6 Training & adoption | Admin handbook (Supered Base) | Owner: Architect | Client-facing: Yes | Start day: 60 | Due day: 85 | Depends on: 5.09 | Lives in: Supered Base | Definition of done: How your portal is set up: naming conventions, properties, workflows, who owns what.
6.05 | P6 Training & adoption | Adoption check #2 | Owner: Architect | Client-facing: No | Start day: 75 | Due day: 75 | Depends on: 6.03 | Lives in: Onboarding record | Definition of done: Same check before the final results review.
7.01 | P7 Run cadence | Office hours (weekly) | Owner: Architect | Client-facing: Yes | Start day: 7 | Due day: 90 | Depends on: 1.09 | Lives in: HubSpot Meetings | Definition of done: Bookable slots via link. Used for questions, coaching and training practice.
7.02 | P7 Run cadence | Weekly update (every Friday) | Owner: Architect | Client-facing: Yes | Start day: 7 | Due day: 90 | Depends on: 4.08 | Lives in: Email logged to onboarding record | Definition of done: AI drafts from completed tasks, Factory progress and KPIs; Architect reviews and sends. See Comms tab for the template.
7.03 | P7 Run cadence | New requests → tickets | Owner: Architect | Client-facing: Yes | Start day: 7 | Due day: 90 | Depends on: - | Lives in: Tickets (Active pipeline) | Definition of done: Every client request becomes a ticket with urgency class. Out of scope → quoted ($250) or saved as 'not now'.
7.04 | P7 Run cadence | Store client ideas as 'not now' | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 90 | Depends on: - | Lives in: Tickets: Not Now | Definition of done: Ideas we won't do now are saved so we can sell them later (fuel for the 'what's next' call).
7.05 | P7 Run cadence | Work scheduled with due dates | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 90 | Depends on: - | Lives in: HubSpot tasks | Definition of done: Every task has a due date and sits in the Architect's task queue / calendar. 'Things we didn't do' are documented, not dropped.
7.06 | P7 Run cadence | Weekly health check | Owner: Architect | Client-facing: No | Start day: 7 | Due day: 90 | Depends on: - | Lives in: Onboarding record | Definition of done: Update status (On track / At risk / Off track), risks & blockers. Escalate per the escalation path.
7.07 | P7 Run cadence | Monthly Business Review (MBR) | Owner: Architect | Client-facing: Yes | Start day: 30 | Due day: 60 | Depends on: 3.03 | Lives in: Meeting | Definition of done: Progress vs benchmark, KPI trend, issues and opportunities found. Phil joins.
7.08 | P7 Run cadence | Internal delivery review (weekly) | Owner: Phil | Client-facing: No | Start day: 7 | Due day: 90 | Depends on: - | Lives in: Board view of onboarding pipeline | Definition of done: Phil + Architects: at-risk customers, capacity, blockers.
8.01 | P8 What's next | Prep next-phase options | Owner: Phil | Client-facing: No | Start day: 55 | Due day: 60 | Depends on: 7.04 | Lives in: Note on onboarding record | Definition of done: Results so far, issues found, 'not now' backlog → Option A / Option B.
8.02 | P8 What's next | 'What's next' call | Owner: Phil | Client-facing: Yes | Start day: 60 | Due day: 65 | Depends on: 8.01 | Lives in: Meeting | Definition of done: Phil explains the customer's next phase with an assumptive A/B choice; Architect joins.
8.03 | P8 What's next | Next-phase proposal | Owner: Phil | Client-facing: Yes | Start day: 62 | Due day: 70 | Depends on: 8.02 | Lives in: Deal | Definition of done: New deal in the Sales Pipeline (type: Expansion) with the chosen option.
8.04 | P8 What's next | Final results review | Owner: Architect | Client-facing: Yes | Start day: 80 | Due day: 88 | Depends on: 5.09 | Lives in: Meeting + dashboard | Definition of done: Before vs after for every progress measure; what we built; what's still open.
8.05 | P8 What's next | Close out the program | Owner: Architect | Client-facing: Yes | Start day: 85 | Due day: 90 | Depends on: 8.04 | Lives in: Onboarding pipeline | Definition of done: Supered plan archived, onboarding → Completed, feedback/NPS and testimonial request.
9.01 | P9 Post-program | 6 months of free KPI monitoring | Owner: Automation | Client-facing: Yes | Start day: 90 | Due day: 270 | Depends on: 8.05 | Lives in: Scheduled dashboard email | Definition of done: Monthly KPI snapshot email (scheduled dashboard) + quarterly check-in.
9.02 | P9 Post-program | Offer: team support | Owner: Phil | Client-facing: Yes | Start day: 60 | Due day: 120 | Depends on: 8.02 | Lives in: Deal | Definition of done: Paid ongoing support for their team.
9.03 | P9 Post-program | Offer: build internal capacity | Owner: Phil | Client-facing: Yes | Start day: 60 | Due day: 120 | Depends on: 8.02 | Lives in: Deal | Definition of done: Paid help to grow their in-house team's skills (training, hiring support).
9.04 | P9 Post-program | Offer: one initiative a month | Owner: Phil | Client-facing: Yes | Start day: 60 | Due day: 120 | Depends on: 8.02 | Lives in: Deal | Definition of done: Ongoing plan, one initiative per month.
9.05 | P9 Post-program | Quarterly relationship check-in | Owner: Phil | Client-facing: Yes | Start day: 120 | Due day: 365 | Depends on: 9.01 | Lives in: Meeting | Definition of done: Goal: keep the relationship for another 6–12 months.

Client Intake Form questions (one per line):
1. [Contacts] Main point of contact (name, email, role) | Field type: Text | Required: Yes | Pre-filled from the deal: Yes (confirm)
2. [Contacts] Supporters who should get updates or training | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: Partly
3. [Contacts] Who controls your DNS / IT? | Field type: Text | Required: Yes | Pre-filled from the deal: No
4. [Contacts] Preferred channel for quick questions | Field type: Dropdown: Email / Slack Connect / Teams | Required: Yes | Pre-filled from the deal: No
5. [Contacts] Time zone and best days for office hours | Field type: Text | Required: No | Pre-filled from the deal: No
6. [Goals] In one sentence: from where to where? (pre-filled from the sale) | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: Yes (confirm)
7. [Goals] Top 3 results you want in the next 90 days | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: Partly
8. [Goals] How do you report marketing results today, and to whom? | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: Partly
9. [Goals] Current numbers: monthly sessions, leads, MQLs, meetings, customers | Field type: Number fields | Required: No | Pre-filled from the deal: Partly
10. [Audience] Who are your buyers? (personas / segments) | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: No
11. [Audience] How do you define a marketing-qualified lead today? | Field type: Multi-line text | Required: Yes | Pre-filled from the deal: No
12. [Marketing today] Channels you use | Field type: Checkboxes: SEO, Paid search, Paid social, Organic social, Email, Events/Webinars, Partners, Outbound | Required: Yes | Pre-filled from the deal: Partly
13. [Marketing today] Campaigns or launches planned in the next 90 days | Field type: Multi-line text | Required: No | Pre-filled from the deal: No
14. [Marketing today] Who on your team will run HubSpot, and hours per week | Field type: Text | Required: Yes | Pre-filled from the deal: Partly
15. [Marketing today] Other agencies or freelancers involved | Field type: Text | Required: No | Pre-filled from the deal: No
16. [Content approval] Who approves emails/pages before they go live, and how fast? | Field type: Text | Required: Yes | Pre-filled from the deal: No
17. [Tech] HubSpot hubs and tiers you own | Field type: Checkboxes per hub + tier | Required: Yes | Pre-filled from the deal: Yes (confirm)
18. [Tech] Website platform and who can edit it | Field type: Dropdown + text | Required: Yes | Pre-filled from the deal: Partly
19. [Tech] Email domain you send from | Field type: Text | Required: Yes | Pre-filled from the deal: No
20. [Tech] Other tools we must connect or migrate from | Field type: Multi-line text (CRM, email tool, ads, webinar, chat, analytics) | Required: Yes | Pre-filled from the deal: Partly
21. [Tech] Where do your contacts live today and roughly how many? | Field type: Text + number | Required: Yes | Pre-filled from the deal: No
22. [Compliance] Regions you market to and consent rules you follow | Field type: Checkboxes: US, Canada (CASL), EU/UK (GDPR), Other | Required: Yes | Pre-filled from the deal: No
23. [Compliance] Industry regulations (e.g. HIPAA, financial) | Field type: Text | Required: No | Pre-filled from the deal: No
24. [Brand] Upload brand guide, logos, fonts, email templates | Field type: File upload | Required: Yes | Pre-filled from the deal: No
25. [Access] Checklist: HubSpot partner access, website admin, GA4/GTM, ad accounts, social accounts | Field type: Checkboxes | Required: Yes | Pre-filled from the deal: Partly

Tech Setup Library rows (one per line, columns separated by |):
Account | Users, teams & permission sets | Tier: S | Task: 4.01 | Owner: Architect | Invite client users, set permissions by role, teams if needed.
Account | Security | Tier: S | Task: 4.01 | Owner: Architect | Require 2FA; SSO on Enterprise.
Account | Account defaults | Tier: S | Task: 4.01 | Owner: Architect | Company info, time zone, currency, fiscal year; brands/business units (Ent).
Tracking | Install tracking code | Tier: S | Task: 4.02 | Owner: Architect | On every domain (CMS plugin or GTM). Verify with a test visit.
Tracking | Exclude internal traffic | Tier: S | Task: 4.02 | Owner: Architect | Client and RevGravy IPs/domains excluded from analytics.
Tracking | Cookie consent banner | Tier: S | Task: 4.02 | Owner: Architect | Configured per regions in intake.
Domains | Connect content domains | Tier: S | Task: 4.03 | Owner: Architect | Landing pages / blog subdomain (e.g. go.client.com).
Domains | Email sending domain authentication | Tier: S | Task: 4.03 | Owner: Architect + client IT | SPF, DKIM, DMARC records added by client DNS contact; verified in HubSpot.
Email | Subscription types | Tier: S | Task: 4.04 | Owner: Architect | Defined per content type; mapped to consent requirements.
Email | Footer, office address, default sender | Tier: S | Task: 4.04 | Owner: Architect | Compliant footer, real sender name.
Email | Brand kit & email templates | Tier: S | Task: 4.04 | Owner: Architect | Logo, colors, fonts; 2–3 reusable templates.
Email | Double opt-in | Tier: S | Task: 4.04 | Owner: Architect | Only if compliance requires it.
Data | Property audit & custom properties | Tier: S | Task: 4.05 | Owner: Architect | Remove unused, add what the Factories need. Naming convention documented.
Data | Lifecycle stages & lead status | Tier: S | Task: 4.05 | Owner: Architect | Definitions agreed with client; automation set.
Data | Marketing contact rules | Tier: S | Task: 4.05 | Owner: Architect | Who is a marketing contact; keeps billing under control.
Data | Import contacts & companies | Tier: S | Task: 4.06 | Owner: Architect | Mapped import, dedupe, associations.
Data | Data hygiene workflows | Tier: P | Task: 4.06 | Owner: Architect | Formatting, required fields, duplicates.
Integrations | Website CMS / non-HubSpot forms | Tier: S | Task: 4.07 | Owner: Architect | Embed or collect external forms.
Integrations | GA4 | Tier: S | Task: 4.07 | Owner: Architect | Connect for reporting.
Integrations | Ad accounts | Tier: S | Task: 4.07 | Owner: Architect | Google, Meta, LinkedIn; conversion events.
Integrations | Social accounts | Tier: S | Task: 4.07 | Owner: Architect | Connect for publishing and reporting.
Integrations | Webinar / Zoom, Slack, other apps | Tier: S | Task: 4.07 | Owner: Architect | As listed in intake.
Integrations | CRM sync (if CRM isn't HubSpot) | Tier: P | Task: 4.07 | Owner: Architect | Field mapping, sync rules, lifecycle alignment.
Integrations | Supered | Tier: S | Task: 1.05 | Owner: Ops | Install and grant client users access.
Lead capture | Forms | Tier: S | Task: 5.01 | Owner: Architect | Hidden fields, consent, progressive fields (Pro).
Lead capture | CTAs / pop-ups | Tier: S | Task: 5.01 | Owner: Architect | Per offer.
Lead capture | Landing & thank-you pages | Tier: S | Task: 5.01 | Owner: Architect | Template + first pages.
Lead capture | Meetings link | Tier: S | Task: 5.01 | Owner: Architect | For sales handoff from nurture.
Segmentation | Core segments | Tier: S | Task: 5.02 | Owner: Architect | Persona, lifecycle, engagement, customers, suppression.
Automation | Nurture workflows | Tier: P | Task: 5.03 | Owner: Architect | Per persona / offer.
Automation | Lead scoring | Tier: P | Task: 5.04 | Owner: Architect | Fit + engagement score; MQL threshold.
Automation | MQL handoff | Tier: P | Task: 5.04 | Owner: Architect | Assignment, notifications, SLA tasks.
Campaigns | Campaigns & UTMs | Tier: P | Task: 5.05 | Owner: Architect | Campaign object, UTM conventions, assets associated.
Campaigns | Ad audiences | Tier: P | Task: 5.06 | Owner: Architect | Retargeting and segment-based audiences.
Reporting | Progress-measure dashboard | Tier: S | Task: 4.08 | Owner: Architect | One report per Factory; baseline vs now.
Reporting | Marketing performance dashboard | Tier: S | Task: 5.07 | Owner: Architect | Traffic, leads, MQLs, emails, campaigns.
Reporting | Attribution reports | Tier: E | Task: 5.07 | Owner: Architect | Multi-touch revenue attribution.
AI | Breeze / AI settings | Tier: S | Task: 5.08 | Owner: Architect | Brand voice, content tools, agents — within agreed AI terms.
QA | End-to-end test | Tier: S | Task: 4.09 | Owner: Architect | Visit → form → contact → workflow → email → notification.
QA | Client sign-off (UAT) | Tier: S | Task: 5.09 | Owner: Client POC | Client approves each delivery before go-live.

Training modules (one per line). Use them as the Module dropdown options in Training Tracker, and have the Task Generator agent create one Training Tracker row per module for each new customer:
T1 · HubSpot basics | Audience: All client users | Format: Supered tour + video | When: After access (≈ Day 7) | Length: 10 min | Navigation, records, notifications, where to find help.
T2 · Contacts & segments | Audience: Marketing team | Format: Video + office hours practice | When: After data import (≈ Day 25) | Length: 20 min | Contact records, properties, segments, data hygiene habits.
T3 · Email marketing | Audience: Marketing team | Format: Video + live build in office hours | When: After email foundations (≈ Day 20) | Length: 25 min | Build, test, send and analyze emails using your templates.
T4 · Forms, landing pages & CTAs | Audience: Marketing team | Format: Video | When: After lead capture ships (≈ Day 40) | Length: 20 min | Create and edit lead capture assets.
T5 · Workflows & nurture | Audience: HubSpot admin(s) | Format: Live session | When: After nurture ships (≈ Day 55) | Length: 30 min | Read, edit and safely clone workflows.
T6 · Campaigns, ads & social | Audience: Marketing team | Format: Video | When: After first campaign (≈ Day 65) | Length: 20 min | Campaign object, UTMs, ads and social reporting.
T7 · Reporting & dashboards | Audience: Marketing lead + leadership | Format: Live at MBR #2 | When: ≈ Day 60 | Length: 20 min | Read the progress-measure dashboard; build a report.
T8 · Lead handoff | Audience: Marketing + sales | Format: Live session | When: After MQL handoff ships (≈ Day 60) | Length: 20 min | MQL definition, notifications, follow-up SLA.
T9 · Admin handbook | Audience: HubSpot admin(s) | Format: Supered Base | When: ≈ Day 85 | Length: Self-serve | How your portal is built and how to maintain it.

When you're done, tell me how many rows each table has. Expect 68 Task Template Library rows, 25 intake questions, 40 Tech Setup Library rows and 9 training modules.
```
