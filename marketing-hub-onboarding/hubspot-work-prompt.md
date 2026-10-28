# HubSpot Work prompt: Marketing Hub Onboarding

`hubspot-work-prompt.txt` has the exact text to paste into HubSpot Work. It only builds structure: the template project, 10 sections, 74 tasks, 44 subtasks, the board and views, a Requests table and a Portfolio for Phil. No agents, documents or forms.

It's generated from `process_data.py` by `build_prompt.py`. Edit the data and re-run the script; don't edit the text by hand.

## How to use it

1. Open HubSpot Work and start a new workspace from a blank prompt.
2. Paste everything in `hubspot-work-prompt.txt`.
3. HubSpot Work shows a plan first. Check the counts against the CHECK line at the end, then approve.
4. For each new customer, duplicate the template project, rename it, fill the project fields, and add a row to the Portfolio.

If HubSpot Work says the prompt is too long, paste everything up to the line "Create these sections and tasks" first. Then send the sections in two or three messages, each starting with "Add these sections and tasks to the Tasks table in the template project:".

## The prompt

```text
Build a workspace called "Client Onboarding" for RevGravy, a HubSpot consultancy. It holds the structure we use to run every Marketing Hub onboarding. Only build the structure described below: projects, task sections, tasks, subtasks, columns, board and views. Do not create agents, documents or forms.

HOW WE WILL USE IT
- Each customer gets a copy of the template project, named "<Client> · Marketing Hub Onboarding".
- Day 0 is the day the customer's deal reaches "Start Payment Received" in our Sales Pipeline.
- Programs last 60 to 90 days. The task days below are for a 90-day program.

PROJECT 1: "Marketing Hub Onboarding (Template)"

Project fields: Company (CRM company); Deal (CRM deal); Architect (HubSpot user); Program length (Dropdown: 60, 75, 90 days); Start date (Date (Day 0)); Target end date (Date); Marketing Hub tier (Dropdown: Professional, Enterprise); Health (Dropdown: On track, At risk, Off track); From→To goal (Long text); FigJam link (URL); Supered Action Plan link (URL).

Table "Tasks" with these columns:
- Task (Text): Task name
- Section (Dropdown): Phase: P0 to P9
- Task ID (Text): e.g. 4.03
- Status (Dropdown): Not started, In progress, Waiting on client, In review, Done, Won't do
- Owner role (Dropdown): Phil, Architect, Ops, Client POC
- Assignee (HubSpot user): Person doing it
- Client-facing (Yes/No): Does the customer see or do this?
- Start day (Number): Days after Day 0 (90-day plan)
- Due day (Number): Days after Day 0 (90-day plan)
- Start date (Date): Set per customer
- Due date (Date): Set per customer (see compression rule)
- Repeats (Text): Weekly, Monthly, etc.
- Depends on (Text): Task IDs
- Definition of done (Long text): What 'done' means
- Notes (Long text): Anything else

Board statuses, in this order: Not started, In progress, Waiting on client, In review, Done, Won't do. Every task starts as "Not started".

Due date rule: Due date = project Start date + Due day. For programs shorter than 90 days, tasks with a Due day above 10 are compressed: Due day × Program length ÷ 90, rounded. Tasks in section P9 are counted from the end instead: Due day − 90 + Program length. Tasks in section P0 get no date. If formula columns are supported, make Due date a formula that follows this rule; if not, leave it empty.

Views on the Tasks table:
- Board: Columns = Status. Cards show Task ID, Task, Assignee, Due date.
- By section: List grouped by Section (P0 → P9), sorted by Task ID.
- Timeline: Start date → Due date, grouped by Section.
- Calendar: By Due date.
- My tasks: Assignee = me, Status not Done / Won't do.
- Client to-dos: Owner role = Client POC, Status not Done.
- This week: Due date in the next 7 days, Status not Done.
- Overdue: Due date before today, Status not Done / Won't do.

Create these sections and tasks, in this order. Put each task in its section and fill Task ID, Owner role, Client-facing, Start day, Due day, Repeats, Depends on and Definition of done ("Done when") from its line. Add the "Subtasks" as a checklist of subtasks under that task.

Section P0 · Handoff checklist (Day -30 to 0)
- 0.01 Research brief from company URL | Owner: Phil | Client-facing: No | before Day 0, check at the handoff
  Done when: Website URL on the deal; research brief attached as a note before the Fit call.
- 0.02 FigJam canvas after Fit call | Owner: Phil | Client-facing: No | before Day 0, check at the handoff | Depends on: 0.01
  Done when: Covers strategic motivation, tactical outcomes, progress measures and fee range. Link saved on the deal.
- 0.03 From→To statement captured | Owner: Phil | Client-facing: No | before Day 0, check at the handoff | Depends on: 0.02
  Done when: One sentence: from where they are today to where they want to be. Every weekly update ties back to it.
- 0.04 Tech stack & team capacity survey | Owner: Client POC | Client-facing: Yes | before Day 0, check at the handoff | Depends on: 0.02
  Done when: Client gave HubSpot access and finished the survey: tools beyond HubSpot, internal processes and cadences, current KPIs.
- 0.05 Products and quote on the deal | Owner: Phil | Client-facing: No | before Day 0, check at the handoff | Depends on: 0.04
  Done when: Pricing calculator used, line items added, quote created. Hub tier is Pro or Enterprise.
- 0.06 Progress measures picked | Owner: Phil | Client-facing: No | before Day 0, check at the handoff | Depends on: 0.05
  Done when: Core set (0.1, 1.1, 1.2, 1.3) plus any optional ones bought (1.0, 2.1). Baselines noted if known.
- 0.07 POC and supporters identified | Owner: Phil | Client-facing: Yes | before Day 0, check at the handoff | Depends on: 0.05
  Done when: Contacts on the deal with labels (POC, Supporter, Billing, Decision maker). POC gets the weekly email.
- 0.08 Agreement signed | Owner: Client POC | Client-facing: Yes | before Day 0, check at the handoff | Depends on: 0.07
  Done when: Includes AI terms, escalation path, how progress is measured, POC and supporters, strategic job → tactical outcomes → progress measures, and request handling ($250 per request, urgency classes).

Section P1 · Close & welcome (Day 0 to 3)
- 1.01 Pick the Architect | Owner: Phil | Client-facing: No | Day 0–1 | Depends on: 0.08
  Done when: Phil checks the capacity view (active customers per Architect) and picks the Architect.
- 1.02 Create the customer project | Owner: Ops | Client-facing: No | Day 0–1 | Depends on: 1.01
  Done when: Duplicate the 'Marketing Hub Onboarding (Template)' project, rename it '<Client> · Marketing Hub Onboarding', fill Company, Deal, Architect, Start date and Program length, and add a Portfolio row.
- 1.03 Welcome email #1: welcome + Action Plan | Owner: Ops | Client-facing: Yes | Day 0 | Depends on: 0.08
  Done when: Sent from Phil on Day 0: Supered Action Plan link, kickoff booking link, first to-dos (grant HubSpot access, fill the intake form).
- 1.04 Build the Supered Action Plan | Owner: Ops | Client-facing: Yes | Day 0–1 | Depends on: 1.02
  Done when: Duplicate the Marketing Hub Action Plan template; add the agreement, FigJam, client to-dos and access checklist.
- 1.05 Phil ↔ Architect handoff (30 min) | Owner: Phil | Client-facing: No | Day 1–3 | Depends on: 1.01
  Done when: Walk through FigJam, customer context, products, the From→To goal, progress measures and KPIs, schedule. Architect checks the Handoff checklist section. Strategy lead moves to the Architect after this call.
- 1.06 Set up progress measures | Owner: Architect | Client-facing: No | Day 1–3 | Depends on: 1.05
  Done when: Add the customer's progress measures to the project (name '<Client> 1.1 Visitor to Lead' etc.) with baseline, target and schedule.
- 1.07 Office hours booking link | Owner: Architect | Client-facing: Yes | Day 1–2 | Depends on: 1.01
  Done when: Architect's HubSpot meetings link (office-hours type) added to the Supered plan.
- 1.08 Welcome email #2: how we work | Owner: Ops | Client-facing: Yes | Day 2 | Depends on: 1.03
  Done when: Day 2: office hours, Friday updates, how to send a request and the urgency classes, escalation path, how we use AI.
- 1.09 Kickoff booked | Owner: Client POC | Client-facing: Yes | Day 0–5 | Depends on: 1.03
  Done when: Client books the 15-minute kickoff from welcome email #1. Chase on Day 3 if not booked.

Section P2 · Access & intake (Day 1 to 7)
- 2.01 HubSpot access granted | Owner: Client POC | Client-facing: Yes | Day 1–3 | Depends on: 1.03
  Done when: Partner access or a Super Admin user for the Architect. Confirm Pro or Enterprise per hub.
- 2.02 Intake form submitted | Owner: Client POC | Client-facing: Yes | Day 1–5 | Depends on: 1.03
  Done when: Short form with only what pre-sale didn't capture (Intake Form tab).
- 2.03 Access to connected systems | Owner: Client POC | Client-facing: Yes | Day 1–7 | Depends on: 2.02
  Done when: DNS/IT contact, website CMS, GA4/GTM, ad accounts, social accounts, and the old email/marketing tool we migrate from.
- 2.04 Brand & content assets shared | Owner: Client POC | Client-facing: Yes | Day 1–7 | Depends on: 2.02
  Done when: Brand guide, logos, fonts, colors, email templates, key content, lists to import.
- 2.05 Supered announcement to POC | Owner: Architect | Client-facing: Yes | Day 2–3 | Depends on: 1.04
  Done when: Short video: how Supered works (Bases, announcements, documentation) and where updates show up.
- 2.06 Portal audit | Owner: Architect | Client-facing: No | Day 3–7 | Depends on: 2.01
  Done when: Data health, email health, existing assets, tracking, workflows, properties, old tool inventory. 1-page summary for kickoff.
- 2.07 Baseline numbers | Owner: Architect | Client-facing: No | Day 5–7 | Depends on: 2.06
  Done when: Record the 'before' number for each progress measure.

Section P3 · Kickoff (Day 5 to 10)
- 3.01 Kickoff agenda | Owner: Architect | Client-facing: No | Day 5–7 | Depends on: 2.02, 2.06
  Done when: Plan summary, missing items, decisions needed. Drafted from intake + audit.
- 3.02 Kickoff session (15 min) | Owner: Architect | Client-facing: Yes | Day 5–10 | Depends on: 3.01
  Done when: Architect & team intro; confirm the goal and plan; walk through missing items; explain office hours, Friday updates, MBRs and how to send requests.
- 3.03 Book MBRs and the 'what's next' call | Owner: Architect | Client-facing: Yes | Day 5–10 | Depends on: 3.02
  Done when: MBR #1 ≈ Day 30, MBR #2 ≈ Day 60, 'what's next' ≈ Day 60–65, final results review ≈ Day 85 (scaled to program length).
- 3.04 Kickoff recap within 24h | Owner: Architect | Client-facing: Yes | Day 6–11 | Depends on: 3.02
  Done when: Decisions, owners, dates, client to-dos. Supered plan updated.

Section P4 · Foundations (Day 7 to 30)
- 4.01 Account, users & security | Owner: Architect | Client-facing: No | Day 7–12 | Depends on: 2.01
  Done when: Users, permission sets, 2FA; Enterprise extras where bought.
  Subtasks: Users & permission sets; Require 2FA; Single sign-on (SSO) (Enterprise only); Brands / business units (Enterprise only); Sandbox account (Enterprise only)
- 4.02 Tracking & consent | Owner: Architect | Client-facing: No | Day 7–14 | Depends on: 2.03
  Done when: Tracking code on every domain, internal traffic excluded, cookie banner set.
  Subtasks: Tracking code on every domain; Exclude internal traffic; Cookie consent banner
- 4.03 Domains & email authentication | Owner: Architect | Client-facing: No | Day 7–18 | Depends on: 2.03
  Done when: Content domain connected; sending domain authenticated (SPF, DKIM, DMARC) with the client's DNS contact.
  Subtasks: Connect content domain; Email sending domain authentication
- 4.04 Email foundations | Owner: Architect | Client-facing: No | Day 10–18 | Depends on: 2.04
  Done when: Subscription types, footer and address, brand kit, email templates, default sender.
  Subtasks: Subscription types; Footer, address, default sender; Brand kit & email templates
- 4.05 Data model | Owner: Architect | Client-facing: No | Day 10–21 | Depends on: 2.06
  Done when: Property audit, lifecycle stage definitions, lead status, marketing-contact rules.
  Subtasks: Property audit; Lifecycle stages & lead status; Marketing contact rules; Custom behavioral events (Enterprise only)
- 4.06 Migration plan & export | Owner: Architect | Client-facing: No | Day 8–16 | Depends on: 2.03
  Done when: Inventory and export from the old tool: lists, consent, unsubscribes and bounces, templates, active automations.
  Subtasks: Old tool inventory; Export lists with consent
- 4.07 Data import & cleanup | Owner: Architect | Client-facing: No | Day 14–25 | Depends on: 4.05, 4.06
  Done when: Import contacts/companies (including migrated lists with consent mapped and unsubscribes suppressed), dedupe, associations, marketing contacts.
  Subtasks: Import contacts & companies; Data hygiene workflows
- 4.08 Website connection | Owner: Architect | Client-facing: No | Day 14–28 | Depends on: 4.02
  Done when: HubSpot forms, CTAs, chat and meetings on the current website; landing page and blog templates.
  Subtasks: HubSpot forms on the site; CTAs, chat & meetings on the site; Landing page & blog templates
- 4.09 Integrations | Owner: Architect | Client-facing: No | Day 14–28 | Depends on: 2.03
  Done when: GA4, ad accounts, social, webinar tool, Slack, CRM sync if their CRM isn't HubSpot.
  Subtasks: GA4; Ad accounts; Social accounts; Webinar, Slack, other apps; CRM sync (if CRM isn't HubSpot)
- 4.10 Baseline dashboard | Owner: Architect | Client-facing: Yes | Day 18–28 | Depends on: 2.07
  Done when: One report per progress measure, showing baseline vs now. Used in every weekly update.
  Subtasks: Baseline dashboard
- 4.11 Foundation QA | Owner: Architect | Client-facing: No | Day 25–30 | Depends on: 4.02, 4.03, 4.04, 4.07
  Done when: Test visit → form → contact → email → notification end to end; test email rendering and deliverability.
  Subtasks: End-to-end test
- 4.12 Supered video: foundations done | Owner: Architect | Client-facing: Yes | Day 28–30 | Depends on: 4.11
  Done when: What changed for the customer and why it matters.

Section P5 · Build & launch (Day 21 to 75)
- 5.01 Build 1.1 Visitor → Lead | Owner: Architect | Client-facing: No | Day 21–40 | Depends on: 4.08, 4.11
  Done when: Forms, CTAs, landing and thank-you pages live on the right pages. Measure: visit-to-contact rate.
  Subtasks: Forms, CTAs, landing & thank-you pages
- 5.02 Build 1.2 Lead → MQL | Owner: Architect | Client-facing: Yes | Day 30–55 | Depends on: 5.01, 4.07
  Done when: Segments, nurture emails and workflows, lead scoring, lifecycle automation. Client approves copy. Measure: lead-to-MQL rate.
  Subtasks: Core segments; Nurture workflows & emails; Lead scoring
- 5.03 Build 1.3 MQL → Meeting | Owner: Architect | Client-facing: Yes | Day 35–60 | Depends on: 5.02
  Done when: MQL definition agreed with sales, owner assignment, notifications, follow-up SLA, meetings link in nurture. Measure: MQL-to-meeting rate.
  Subtasks: MQL handoff
- 5.04 Build 2.1 Subscriber → Engaged (if bought) | Owner: Architect | Client-facing: No | Day 35–60 | Depends on: 4.04
  Done when: Newsletter or content program, subscription preferences, re-engagement and sunset flows. Measure: email click rate, engaged contacts.
  Subtasks: Re-engagement & sunset flows
- 5.05 Build 1.0 Stranger → Visitor (if bought) | Owner: Architect | Client-facing: No | Day 30–60 | Depends on: 4.09
  Done when: Campaigns and UTMs, ad audiences and conversion events, social publishing, SEO recommendations. Measure: sessions by source.
  Subtasks: Campaigns, UTMs & ad audiences
- 5.06 Migration: rebuild and switch off old tool | Owner: Architect | Client-facing: Yes | Day 25–50 | Depends on: 4.06, 4.07
  Done when: Rebuild templates and active automations from the old tool, send in parallel once, then switch the old tool off.
  Subtasks: Rebuild templates & automations; Parallel send, then switch off the old tool
- 5.07 Website: landing pages & blog | Owner: Architect | Client-facing: Yes | Day 30–60 | Depends on: 4.08
  Done when: Migrate landing pages and blog posts within the agreed limit; redirects set.
  Subtasks: Migrate landing pages & blog
- 5.08 First campaign live | Owner: Architect | Client-facing: Yes | Day 40–65 | Depends on: 5.01, 5.02
  Done when: Campaign with UTMs and assets, launched with the client.
- 5.09 Performance reporting | Owner: Architect | Client-facing: Yes | Day 45–70 | Depends on: 4.10
  Done when: Marketing performance dashboard and funnel by progress measure; revenue attribution on Enterprise.
  Subtasks: Marketing performance dashboard; Revenue attribution reports (Enterprise only)
- 5.10 AI / Breeze setup | Owner: Architect | Client-facing: No | Day 45–70 | Depends on: 4.04
  Done when: Brand voice and content tools, only within the AI terms in the agreement.
  Subtasks: Breeze / AI settings
- 5.11 Client sign-off per progress measure | Owner: Client POC | Client-facing: Yes | Day 35–75 | Depends on: 5.01–5.07
  Done when: Client approves each build before it goes live.
- 5.12 Supered video per delivery | Owner: Architect | Client-facing: Yes | Day 35–75 | Repeats: After each delivery | Depends on: 5.11
  Done when: What was built, how to use it, why it matters.

Section P6 · Training & adoption (Day 14 to 85)
- 6.01 Confirm training plan | Owner: Architect | Client-facing: Yes | Day 10–14 | Depends on: 2.02
  Done when: Who needs which modules (Training tab), from the intake.
- 6.02 Deliver training modules | Owner: Architect | Client-facing: Yes | Day 14–85 | Depends on: 6.01
  Done when: Supered videos + practice in office hours, timed to when each feature ships.
- 6.03 Adoption check #1 | Owner: Architect | Client-facing: No | Day 45 | Depends on: 6.02
  Done when: Logins, emails sent, workflows active, dashboards viewed. Flag low adoption in the weekly update.
- 6.04 Admin handbook (Supered Base) | Owner: Architect | Client-facing: Yes | Day 60–85 | Depends on: 5.11
  Done when: How the portal is set up: naming, properties, workflows, who owns what.
- 6.05 Adoption check #2 | Owner: Architect | Client-facing: No | Day 75 | Depends on: 6.03
  Done when: Same check before the final results review.

Section P7 · Run cadence (Day 7 to 90)
- 7.01 Office hours | Owner: Architect | Client-facing: Yes | Day 7–90 | Repeats: Weekly | Depends on: 1.07
  Done when: Bookable slots for questions, coaching and training practice.
- 7.02 Weekly update | Owner: Architect | Client-facing: Yes | Day 7–90 | Repeats: Weekly (Friday) | Depends on: 4.10
  Done when: Drafted with AI, reviewed and sent by the Architect: work done and the strategic issue it moves, numbers vs baseline, issues found outside scope, next week, client to-dos.
- 7.03 Handle requests by urgency | Owner: Architect | Client-facing: Yes | Day 7–90 | Repeats: As they come in
  Done when: Every request gets logged with an urgency class and handled in that time ($250 per request; see Request Classes).
- 7.04 Log issues and 'not now' ideas | Owner: Architect | Client-facing: No | Day 7–90 | Repeats: As they come in
  Done when: Out-of-scope issues and client ideas go to the Requests table as 'Not now', to sell later.
- 7.05 Health check | Owner: Architect | Client-facing: No | Day 7–90 | Repeats: Weekly
  Done when: Set Health (On track / At risk / Off track) and blockers. Escalate per the escalation path.
- 7.06 Monthly Business Review | Owner: Architect | Client-facing: Yes | Day 30–60 | Repeats: Monthly | Depends on: 3.03
  Done when: Progress vs baseline, numbers trend, issues and opportunities. Architect leads; Phil optional.
- 7.07 Internal delivery review | Owner: Phil | Client-facing: No | Day 7–90 | Repeats: Weekly
  Done when: Phil + Architects: at-risk customers, capacity, blockers.

Section P8 · What's next (Day 60 to 90)
- 8.01 Prep next-phase options | Owner: Architect | Client-facing: No | Day 55–60 | Depends on: 7.04
  Done when: Results so far, issues found and 'not now' list → Option A and Option B. Phil reviews.
- 8.02 'What's next' call | Owner: Phil | Client-facing: Yes | Day 60–65 | Depends on: 8.01
  Done when: Phil explains the next phase with an A/B choice; Architect joins.
- 8.03 Next-phase proposal | Owner: Phil | Client-facing: Yes | Day 62–70 | Depends on: 8.02
  Done when: New deal in the Sales Pipeline for the chosen offer.
- 8.04 Final results review | Owner: Architect | Client-facing: Yes | Day 80–88 | Depends on: 5.11
  Done when: Before vs after for every progress measure, what we built, what's still open.
- 8.05 Close the program | Owner: Architect | Client-facing: Yes | Day 85–90 | Depends on: 8.04
  Done when: Supered plan archived, project marked Completed, feedback and testimonial asked for.

Section P9 · After the program (Day 90 to 270)
- 9.01 Monthly KPI snapshot | Owner: Architect | Client-facing: Yes | Day 90–270 | Repeats: Monthly × 6 | Depends on: 8.05
  Done when: Progress-measure dashboard emailed with 3 short notes from the Architect.
- 9.02 Portal health alerts | Owner: Architect | Client-facing: Yes | Day 90–270 | Repeats: Ongoing | Depends on: 8.05
  Done when: Watch for deliverability drops, workflow errors, form submissions down 30%+. Tell the client when one fires.
- 9.03 Check-in call: month 3 | Owner: Architect | Client-facing: Yes | Day 180 | Depends on: 9.01
  Done when: 30 minutes: numbers, what's working, what's next.
- 9.04 Paid offer conversation: month 5 | Owner: Phil | Client-facing: Yes | Day 240 | Depends on: 9.03
  Done when: Present team support, internal capacity and one-initiative-a-month before monitoring ends.
- 9.05 Check-in call: month 6 | Owner: Architect | Client-facing: Yes | Day 270 | Depends on: 9.04
  Done when: Final monitoring check-in; confirm the paid offer or close monitoring.

Table "Requests" (in the same project) with these columns: Request (Text); Urgency (Dropdown: Critical, High, Standard, Not now); Type (Dropdown: Client request, Issue found, Client idea); Status (Dropdown: New, Quoted, In progress, Done, Parked); Price (Number (default 250)); Logged on (Date); Due date (Date); Notes (Long text).
Views on Requests: "Board by urgency" (columns = Urgency) and "Open requests" (Status not Done or Parked, sorted by Due date).
Use these as the descriptions of the Urgency options:
- Critical: Something live is broken: forms not submitting, emails not sending, a workflow sending the wrong email, tracking down. Reply within 4 business hours; fixed within 1 business day. Price: Free if it's in something we built; otherwise $250.
- High: Needed for a launch or deadline in the next 2 weeks. Started within 2 business days; done within 5. Price: $250.
- Standard: A small new request with no hard deadline. Planned into next week; done within 10 business days. Price: $250.
- Not now: An idea or a bigger project for later. Logged and reviewed at MBRs and the 'what's next' call. Price: Quoted when scoped.

PROJECT 2: "Onboarding Portfolio"

Table "Customers", one row per customer, with these columns: Customer (Text (link to the customer project)); Company (CRM company); Architect (HubSpot user); Program length (60, 75, 90 days); Start date (Date); Target end date (Date); Current section (Dropdown P0–P9, Completed); Health (On track, At risk, Off track); Next MBR (Date); Next due task (Text).
Views:
- Capacity: Grouped by Architect, only active customers, with a count per group. Phil uses this to pick the Architect.
- Health board: Columns = Health.
- Ending soon: Target end date in the next 35 days (time for the 'what's next' call).

CHECK
When you show me the plan, confirm the counts: 2 projects, 10 sections, 74 tasks, 44 subtasks, 8 views on Tasks, 1 Requests table. Show me the plan and wait for my approval before you create anything.
```
