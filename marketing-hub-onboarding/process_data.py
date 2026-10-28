"""Single source of truth for the RevGravy Marketing Hub Onboarding process.

Both build_workbook.py (the sheet) and build_roadmap.py (the visual roadmap)
read from this file, so edit the process here and re-run both scripts.

Day offsets are counted from Day 0 = deal reaches "Start Payment Received"
(the closed-won stage of the Sales Pipeline). The program targets 90 days
(confirmed); some customers may run longer, so treat offsets as targets.
"""

PROGRAM_DAYS = 90

ROLES = {
    "Phil": "Strategy lead. Owns the sale, the Architect handoff, MBR strategy and the 'what's next' conversation.",
    "Architect": "Assigned delivery lead. Owns the onboarding record, the build, weekly updates and office hours.",
    "Ops": "RevGravy operations/admin. Owns templates, Supered setup, data hygiene of the process itself.",
    "AI": "AI agent drafts (handoff brief, agendas, weekly updates). A human always reviews before anything is sent.",
    "Automation": "HubSpot workflow, no human action needed.",
    "Client POC": "Main point of contact at the customer. Owns approvals, access and client to-dos.",
    "Client team": "Supporters / end users at the customer who get trained and use the portal.",
}

# Each phase maps back to one or more stickies on the FigJam board.
PHASES = [
    {
        "id": "P0", "name": "Pre-sale handoff", "start": -30, "end": 0,
        "figjam": "New Lead → VSL → Fit/Discovery → Assess Tech Stack → Video → Recommendation → Closing Call",
        "goal": "Everything the Architect needs is already on the deal before the customer pays (Definition of Ready).",
        "client_sees": "VSL, recommendation video, proposal Q&A, quote, agreement.",
        "exit": "Deal has FigJam link, From→To statement, products, progress measures, survey, POC and supporters, signed agreement.",
    },
    {
        "id": "P1", "name": "Close & welcome", "start": 0, "end": 3,
        "figjam": "Paid & Agreement Signed",
        "goal": "Customer feels the handoff instantly; the Architect is assigned and briefed within 72 hours.",
        "client_sees": "Welcome email series with the Supered Action Plan (expectations, next steps, links, agreement, to-dos).",
        "exit": "Architect assigned, Phil↔Architect 1:1 done, Delivery Template instantiated, kickoff booked.",
    },
    {
        "id": "P2", "name": "Access & intake", "start": 1, "end": 7,
        "figjam": "HS Access / Form / Trello",
        "goal": "Get every access and input we need in week 1, and replace Trello with HubSpot + Supered.",
        "client_sees": "Supered announcement explaining how we deliver announcements and documentation; one short intake form.",
        "exit": "Portal access granted, intake submitted, audit and baseline KPIs captured.",
    },
    {
        "id": "P3", "name": "Kickoff", "start": 5, "end": 10,
        "figjam": "Kickoff Session 15 min",
        "goal": "15 minutes that confirm the plan, close gaps and set the operating rhythm.",
        "client_sees": "Architect + team intro, confirmed plan, office hours and MBRs explained, MBRs booked.",
        "exit": "Plan confirmed, missing items owned, MBR dates on calendars, recap sent within 24h.",
    },
    {
        "id": "P4", "name": "Foundations (tech setup)", "start": 7, "end": 30,
        "figjam": "Delivery Template → technical setup",
        "goal": "Marketing Hub is set up correctly: tracking, domains, email auth, data model, imports, baseline reporting.",
        "client_sees": "Supered video announcements as each foundation item is done; weekly updates.",
        "exit": "Foundation QA passed and a baseline dashboard exists to report progress measures against.",
    },
    {
        "id": "P5", "name": "Build & launch", "start": 21, "end": 75,
        "figjam": "Tactical outcomes / Factories (progress measures)",
        "goal": "Ship the tactical outcomes the customer bought, each tied to a progress measure.",
        "client_sees": "Supered video per delivery, UAT sign-off requests, KPI movement in weekly updates.",
        "exit": "Every Factory in the Delivery Template is live, approved and reporting.",
    },
    {
        "id": "P6", "name": "Training & adoption", "start": 14, "end": 85,
        "figjam": "Office Hours / Supered videos",
        "goal": "The customer's team can run what we built without us.",
        "client_sees": "Short Supered training videos per delivery, office-hours coaching, an admin handbook.",
        "exit": "Each user role completed its modules; adoption check passed.",
    },
    {
        "id": "P7", "name": "Run cadence", "start": 7, "end": 90,
        "figjam": "Office Hours + Weekly updates",
        "goal": "A predictable rhythm: office hours, Friday updates, monthly business reviews, managed requests.",
        "client_sees": "Weekly update (progress, tactical work → strategic issue, KPIs, issues found), office hours, MBRs.",
        "exit": "Runs every week until the program ends.",
    },
    {
        "id": "P8", "name": "What's next", "start": 60, "end": 90,
        "figjam": "30 Days Before We Finish, Explain What's Next",
        "goal": "Customer sees the long-term vision and chooses the next phase before the program ends.",
        "client_sees": "'What's next' call with Phil and the Architect, A/B next-phase options, final results review.",
        "exit": "Next-phase decision made (A, B or offboard), results review delivered, project closed.",
    },
    {
        "id": "P9", "name": "Post-program", "start": 90, "end": 365,
        "figjam": "Post-1st Program Offers + Goal: keep relationship 6–12 months",
        "goal": "Keep the relationship for 6–12 more months.",
        "client_sees": "6 months of free KPI monitoring, ongoing offers, quarterly check-ins.",
        "exit": "Customer on a continuation offer, or a clean offboarding with KPI monitoring running.",
    },
]

# Columns: id, phase, task, details / definition of done, owner, client_facing,
#          start_day, due_day, depends_on, lives_in, automation
TASKS = [
    # P0 — Pre-sale handoff (Definition of Ready). These are gates on the deal, not post-sale work.
    ("0.01", "P0", "Research brief from company URL", "Website URL on the deal; AI research brief attached as a note before the Fit call.", "AI", "No", -30, -28, "", "Deal (note)", "AI agent drafts brief when deal is created"),
    ("0.02", "P0", "FigJam canvas created after Fit call", "Canvas covers strategic motivation, tactical outcomes, progress measures and fee range. Link saved to the deal and later copied to the onboarding record.", "Phil", "No", -25, -21, "0.01", "Deal property: Canvas / FigJam Link", ""),
    ("0.03", "P0", "Strategic motivation captured ('From X to Y')", "One sentence: from where they are today to where they want to be. This is the north star the weekly updates tie back to.", "Phil", "No", -25, -21, "0.02", "Deal property", ""),
    ("0.04", "P0", "Tech stack & team capacity survey completed", "Client gives HubSpot access and completes the survey (form or AI chat): tools beyond HubSpot, internal processes and cadences, current KPIs and progress measures.", "Client POC", "Yes", -21, -14, "0.02", "Form → Deal/Company properties", "Survey reminder email after 2 days"),
    ("0.05", "P0", "Products and quote on the deal", "Pricing calculator used; line items added; quote created.", "Phil", "No", -14, -10, "0.04", "Deal line items + Quote", ""),
    ("0.06", "P0", "Progress measures defined", "Each tactical outcome has a progress measure (Factory) with a baseline if known.", "Phil", "No", -14, -7, "0.05", "Deal note → Factory records after close", ""),
    ("0.07", "P0", "POC and supporters identified", "Contacts associated to the deal with association labels (POC, Supporter, Billing, Decision maker). POC enrolled in the weekly email.", "Phil", "Yes", -10, -3, "0.05", "Contact ↔ Deal association labels", ""),
    ("0.08", "P0", "Agreement signed", "Includes AI terms, escalation path, how progress is measured, main POC and supporters, strategic job → tactical outcomes → progress measures, and new-request handling with urgency classification ($250).", "Client POC", "Yes", -5, 0, "0.07", "Quote / e-signature", ""),
    ("0.09", "P0", "Definition of Ready gate", "Deal cannot move to 'Start Payment Received' unless the required handoff properties are filled.", "Automation", "No", 0, 0, "0.08", "Deal stage required properties", "Required properties on stage"),

    # P1 — Close & welcome
    ("1.01", "P1", "Create onboarding record", "Deal reaches 'Start Payment Received' → onboarding record created from the Marketing Hub template and associated to deal, company and contacts; deal context copied over.", "Automation", "No", 0, 0, "0.09", "Onboarding record + workflow", "Deal-stage workflow"),
    ("1.02", "P1", "Assign Architect", "Phil picks the Architect (or rotation by capacity). Architect becomes owner of the onboarding record and company.", "Phil", "No", 0, 1, "1.01", "Onboarding record owner", "Notify Phil if unassigned after 24h"),
    ("1.03", "P1", "Notify team with handoff brief", "Slack + HubSpot notification to the delivery team. AI drafts the brief from deal history, FigJam and survey.", "AI", "No", 0, 1, "1.02", "Slack + Note on onboarding record", "Workflow + AI agent"),
    ("1.04", "P1", "Welcome email #1: welcome + Action Plan", "Sent from Phil. Links to the Supered Action Plan: expectations, next steps, how the partnership works, agreement, client to-dos, kickoff booking link.", "Automation", "Yes", 0, 0, "1.01", "Marketing email / sequence", "Deal-stage workflow"),
    ("1.05", "P1", "Build Supered Action Plan from template", "Duplicate the Marketing Hub Action Plan template. Add the agreement, FigJam, client to-dos and access checklist.", "Ops", "Yes", 0, 1, "1.01", "Supered", ""),
    ("1.06", "P1", "Instantiate Delivery Template", "Create one Factory (progress measure) record per tactical outcome bought, with benchmark, schedule and client to-dos.", "Architect", "No", 1, 3, "1.02", "Factory records (Projects object)", "Optional: workflow creates Factories from line items"),
    ("1.07", "P1", "Set internal progress measures", "Planned end date, hours budget, health = On track, next MBR date.", "Ops", "No", 0, 1, "1.01", "Onboarding record properties", ""),
    ("1.08", "P1", "Phil ↔ Architect 1:1 handoff (30 min)", "Walk through FigJam, customer context, products chosen, the goal, outcomes, how success is measured (KPIs), the Delivery Template and schedule.", "Phil", "No", 1, 3, "1.02", "Meeting on onboarding record", "Task auto-created for Phil"),
    ("1.09", "P1", "Office hours booking link ready", "Architect's HubSpot Meetings link (office-hours type) added to the Supered plan.", "Architect", "Yes", 1, 2, "1.02", "HubSpot Meetings", ""),
    ("1.10", "P1", "Welcome email #2: how we work", "Office hours, weekly updates, how to request work and the urgency classes, escalation path, how we use AI.", "Automation", "Yes", 2, 2, "1.04", "Marketing email / sequence", "Delay 2 days"),
    ("1.11", "P1", "Kickoff booked", "Client books the 15-minute kickoff via the link in welcome email #1. Reminder at Day 3 if not booked.", "Client POC", "Yes", 0, 5, "1.04", "Meeting", "Reminder if no meeting by Day 3"),

    # P2 — Access & intake
    ("2.01", "P2", "HubSpot access granted", "Partner access or a Super Admin user for the Architect. Confirm the hub tiers (Marketing Starter / Pro / Enterprise).", "Client POC", "Yes", 1, 3, "1.04", "Client to-do in Supered", "Reminder on Day 3"),
    ("2.02", "P2", "Onboarding intake form submitted", "Short form that asks only what pre-sale didn't capture (see Intake Form tab).", "Client POC", "Yes", 1, 5, "1.04", "Form → onboarding record", "Reminder on Day 4"),
    ("2.03", "P2", "Access to connected systems", "DNS/IT contact, website CMS, GA4/GTM, ad accounts, social accounts, any CRM or email tool we migrate from.", "Client POC", "Yes", 1, 7, "2.02", "Access checklist (intake)", ""),
    ("2.04", "P2", "Brand & content assets shared", "Brand guide, logos, fonts, colors, existing email templates, key content, lists to import.", "Client POC", "Yes", 1, 7, "2.02", "File upload on intake form", ""),
    ("2.05", "P2", "Supered announcement to POC", "Short video: how Supered works (Bases, announcements, documentation) and where updates will show up.", "Architect", "Yes", 2, 3, "1.05", "Supered", ""),
    ("2.06", "P2", "Portal audit (current state)", "Data health, email health, existing assets, tracking code, workflows, properties. Output: 1-page audit summary for kickoff.", "Architect", "No", 3, 7, "2.01", "Note on onboarding record", "AI can draft from portal scan"),
    ("2.07", "P2", "Baseline KPI snapshot", "Record the 'before' numbers for each progress measure (sessions, leads, MQLs, meetings, etc.).", "Architect", "No", 5, 7, "2.06", "Factory records: baseline", ""),
    ("2.08", "P2", "No Trello", "All delivery work lives in HubSpot (tasks on the onboarding record) and client-facing docs in Supered. Architect owns this.", "Architect", "No", 1, 1, "", "Policy", ""),

    # P3 — Kickoff
    ("3.01", "P3", "Kickoff agenda drafted", "AI drafts from intake + audit: plan summary, missing items, decisions needed. Architect edits.", "AI", "No", 5, 7, "2.02, 2.06", "Doc / note", ""),
    ("3.02", "P3", "Kickoff session (15 min)", "Architect & team intro; confirm goal and 90-day plan; walk through missing items; explain office hours, weekly updates, MBRs and request process.", "Architect", "Yes", 5, 10, "3.01", "Meeting", ""),
    ("3.03", "P3", "Book MBRs and the 'what's next' call", "MBR #1 ≈ Day 30, MBR #2 ≈ Day 60 (includes what's next), final results review ≈ Day 85.", "Architect", "Yes", 5, 10, "3.02", "Meetings", ""),
    ("3.04", "P3", "Kickoff recap within 24h", "AI drafts the recap; Architect sends. Supered plan updated with confirmed schedule and client to-dos.", "Architect", "Yes", 6, 11, "3.02", "Email + Supered", ""),
    ("3.05", "P3", "Move onboarding to Foundations", "Stage = Foundations, health set.", "Architect", "No", 6, 11, "3.02", "Onboarding pipeline stage", ""),

    # P4 — Foundations
    ("4.01", "P4", "Account settings, users & permissions", "Users, teams, permission sets, 2FA, account defaults, brands/business units if relevant.", "Architect", "No", 7, 12, "2.01", "Tech Setup tab", ""),
    ("4.02", "P4", "Tracking code & consent", "Tracking code on every site domain, internal IPs excluded, cookie consent banner configured.", "Architect", "No", 7, 14, "2.03", "Tech Setup tab", ""),
    ("4.03", "P4", "Domains & email authentication", "Connect landing page / blog domains; authenticate the email sending domain (SPF, DKIM, DMARC). Needs client DNS contact.", "Architect", "No", 7, 18, "2.03", "Tech Setup tab", ""),
    ("4.04", "P4", "Email foundations", "Subscription types, footer and office address, brand kit, email templates, default sender.", "Architect", "No", 10, 18, "2.04", "Tech Setup tab", ""),
    ("4.05", "P4", "Data model", "Property audit, custom properties, lifecycle stage definitions, lead status, marketing-contact rules.", "Architect", "No", 10, 21, "2.06", "Tech Setup tab", ""),
    ("4.06", "P4", "Data import & cleanup", "Import contacts/companies, dedupe, associations, set marketing contacts.", "Architect", "No", 14, 25, "4.05", "Tech Setup tab", ""),
    ("4.07", "P4", "Integrations", "Website forms, GA4, ad accounts, social, webinar/Zoom, Slack, CRM sync if the CRM isn't HubSpot.", "Architect", "No", 14, 28, "2.03", "Tech Setup tab", ""),
    ("4.08", "P4", "Baseline progress dashboard", "Dashboard with one report per progress measure, so weekly updates can show KPIs.", "Architect", "Yes", 18, 28, "2.07", "HubSpot dashboard", ""),
    ("4.09", "P4", "Foundation QA", "Test tracking, a test email (deliverability + rendering), test form submission end to end.", "Architect", "No", 25, 30, "4.02, 4.03, 4.04", "QA checklist", ""),
    ("4.10", "P4", "Supered announcement: foundations done", "Short video: what changed for you and why it matters.", "Architect", "Yes", 28, 30, "4.09", "Supered", ""),

    # P5 — Build & launch (repeat per Factory)
    ("5.01", "P5", "Lead capture", "Forms, CTAs/pop-ups, landing pages, thank-you pages, meetings link.", "Architect", "No", 21, 40, "4.09", "Factory: Visitor → Lead", ""),
    ("5.02", "P5", "Segmentation", "Segments by persona, lifecycle and engagement; suppression lists.", "Architect", "No", 25, 40, "4.06", "Factory", ""),
    ("5.03", "P5", "Lead nurture", "Nurture workflows and emails per persona/offer. Client approves copy.", "Architect", "Yes", 30, 55, "5.01, 5.02", "Factory: Lead → MQL", ""),
    ("5.04", "P5", "Lifecycle automation & MQL handoff", "Lead scoring (Pro+), MQL criteria, owner assignment, sales notifications, follow-up SLA.", "Architect", "Yes", 35, 60, "4.05", "Factory: MQL → Meeting", ""),
    ("5.05", "P5", "First campaign live", "Campaign object, UTMs, assets associated, launched with the client.", "Architect", "Yes", 40, 65, "5.01, 5.03", "Factory", ""),
    ("5.06", "P5", "Ads & social", "Connect ad accounts, conversion events, audiences (Pro+), social publishing.", "Architect", "No", 30, 60, "4.07", "Factory", ""),
    ("5.07", "P5", "Performance reporting", "Marketing performance dashboard, funnel by progress measure, attribution (Pro/Ent).", "Architect", "Yes", 45, 70, "4.08", "HubSpot dashboard", ""),
    ("5.08", "P5", "AI / Breeze configuration", "Brand voice, content tools and agents, only within the AI terms in the agreement.", "Architect", "No", 45, 70, "4.04", "Tech Setup tab", ""),
    ("5.09", "P5", "UAT & go-live per Factory", "Client reviews and approves each delivery; Factory moves to Done.", "Client POC", "Yes", 35, 75, "5.01–5.08", "Factory record stage", ""),
    ("5.10", "P5", "Supered video per delivery", "What was built, how to use it, why it matters.", "Architect", "Yes", 35, 75, "5.09", "Supered", ""),
    ("5.11", "P5", "Log issues found & out of scope", "Anything uncovered that's not in scope becomes a ticket ('sell the problem') or a 'not now' item.", "Architect", "No", 7, 90, "", "Tickets", ""),

    # P6 — Training & adoption
    ("6.01", "P6", "Confirm training plan", "Who needs which modules (from intake). See Training tab.", "Architect", "Yes", 10, 14, "2.02", "Training tab", ""),
    ("6.02", "P6", "Deliver training modules", "Supered videos + live practice in office hours, timed to when each feature ships.", "Architect", "Yes", 14, 85, "6.01", "Supered + office hours", ""),
    ("6.03", "P6", "Adoption check #1", "Logins, emails sent, workflows active, dashboards viewed. Flag low adoption in the weekly update.", "Architect", "No", 45, 45, "6.02", "Onboarding record", "Task auto-created Day 45"),
    ("6.04", "P6", "Admin handbook (Supered Base)", "How your portal is set up: naming conventions, properties, workflows, who owns what.", "Architect", "Yes", 60, 85, "5.09", "Supered Base", ""),
    ("6.05", "P6", "Adoption check #2", "Same check before the final results review.", "Architect", "No", 75, 75, "6.03", "Onboarding record", "Task auto-created Day 75"),

    # P7 — Run cadence (recurring)
    ("7.01", "P7", "Office hours (weekly)", "Bookable slots via link. Used for questions, coaching and training practice.", "Architect", "Yes", 7, 90, "1.09", "HubSpot Meetings", ""),
    ("7.02", "P7", "Weekly update (every Friday)", "AI drafts from completed tasks, Factory progress and KPIs; Architect reviews and sends. See Comms tab for the template.", "Architect", "Yes", 7, 90, "4.08", "Email logged to onboarding record", "Recurring task every Thursday + AI draft"),
    ("7.03", "P7", "New requests → tickets", "Every client request becomes a ticket with urgency class. Out of scope → quoted ($250) or saved as 'not now'.", "Architect", "Yes", 7, 90, "", "Tickets (Active pipeline)", "Form/email → ticket"),
    ("7.04", "P7", "Store client ideas as 'not now'", "Ideas we won't do now are saved so we can sell them later (fuel for the 'what's next' call).", "Architect", "No", 7, 90, "", "Tickets: Not Now", ""),
    ("7.05", "P7", "Work scheduled with due dates", "Every task has a due date and sits in the Architect's task queue / calendar. 'Things we didn't do' are documented, not dropped.", "Architect", "No", 7, 90, "", "HubSpot tasks", ""),
    ("7.06", "P7", "Weekly health check", "Update status (On track / At risk / Off track), risks & blockers. Escalate per the escalation path.", "Architect", "No", 7, 90, "", "Onboarding record", "Alert Phil when At risk"),
    ("7.07", "P7", "Monthly Business Review (MBR)", "Progress vs benchmark, KPI trend, issues and opportunities found. Phil joins.", "Architect", "Yes", 30, 60, "3.03", "Meeting", ""),
    ("7.08", "P7", "Internal delivery review (weekly)", "Phil + Architects: at-risk customers, capacity, blockers.", "Phil", "No", 7, 90, "", "Board view of onboarding pipeline", ""),

    # P8 — What's next
    ("8.01", "P8", "Prep next-phase options", "Results so far, issues found, 'not now' backlog → Option A / Option B.", "Phil", "No", 55, 60, "7.04", "Note on onboarding record", "AI drafts summary"),
    ("8.02", "P8", "'What's next' call", "Phil explains the customer's next phase with an assumptive A/B choice; Architect joins.", "Phil", "Yes", 60, 65, "8.01", "Meeting", ""),
    ("8.03", "P8", "Next-phase proposal", "New deal in the Sales Pipeline (type: Expansion) with the chosen option.", "Phil", "Yes", 62, 70, "8.02", "Deal", ""),
    ("8.04", "P8", "Final results review", "Before vs after for every progress measure; what we built; what's still open.", "Architect", "Yes", 80, 88, "5.09", "Meeting + dashboard", ""),
    ("8.05", "P8", "Close out the program", "Supered plan archived, onboarding → Completed, feedback/NPS and testimonial request.", "Architect", "Yes", 85, 90, "8.04", "Onboarding pipeline", "Feedback survey on stage change"),

    # P9 — Post-program
    ("9.01", "P9", "6 months of free KPI monitoring", "Monthly KPI snapshot email (scheduled dashboard) + quarterly check-in.", "Automation", "Yes", 90, 270, "8.05", "Scheduled dashboard email", "Monthly"),
    ("9.02", "P9", "Offer: team support", "Paid ongoing support for their team.", "Phil", "Yes", 60, 120, "8.02", "Deal", ""),
    ("9.03", "P9", "Offer: build internal capacity", "Paid help to grow their in-house team's skills (training, hiring support).", "Phil", "Yes", 60, 120, "8.02", "Deal", ""),
    ("9.04", "P9", "Offer: one initiative a month", "Ongoing plan, one initiative per month.", "Phil", "Yes", 60, 120, "8.02", "Deal", ""),
    ("9.05", "P9", "Quarterly relationship check-in", "Goal: keep the relationship for another 6–12 months.", "Phil", "Yes", 120, 365, "9.01", "Meeting", "Task every 90 days"),
]

# section, question, field type, required, already captured pre-sale?, why we ask, maps to
INTAKE = [
    ("Contacts", "Main point of contact (name, email, role)", "Text", "Yes", "Yes (confirm)", "One owner for approvals and to-dos.", "Contact + association label POC"),
    ("Contacts", "Supporters who should get updates or training", "Multi-line text", "Yes", "Partly", "Training plan and weekly update recipients.", "Contacts + association label Supporter"),
    ("Contacts", "Who controls your DNS / IT?", "Text", "Yes", "No", "Needed for email authentication and domain connection.", "Onboarding: DNS contact"),
    ("Contacts", "Preferred channel for quick questions", "Dropdown: Email / Slack Connect / Teams", "Yes", "No", "Sets how office-hours follow-ups happen.", "Onboarding: Comms channel"),
    ("Contacts", "Time zone and best days for office hours", "Text", "No", "No", "Office hours slots.", "Onboarding: Time zone"),
    ("Goals", "In one sentence: from where to where? (pre-filled from the sale)", "Multi-line text", "Yes", "Yes (confirm)", "The strategic motivation every update ties back to.", "Onboarding: Customer goal"),
    ("Goals", "Top 3 results you want in the next 90 days", "Multi-line text", "Yes", "Partly", "Prioritizes the Delivery Template.", "Onboarding: Success metrics"),
    ("Goals", "How do you report marketing results today, and to whom?", "Multi-line text", "Yes", "Partly", "Shapes dashboards and MBRs.", "Onboarding note"),
    ("Goals", "Current numbers: monthly sessions, leads, MQLs, meetings, customers", "Number fields", "No", "Partly", "Baseline for progress measures.", "Factory baseline"),
    ("Audience", "Who are your buyers? (personas / segments)", "Multi-line text", "Yes", "No", "Segmentation and nurture design.", "Onboarding note"),
    ("Audience", "How do you define a marketing-qualified lead today?", "Multi-line text", "Yes", "No", "Lifecycle and MQL handoff.", "Onboarding note"),
    ("Marketing today", "Channels you use", "Checkboxes: SEO, Paid search, Paid social, Organic social, Email, Events/Webinars, Partners, Outbound", "Yes", "Partly", "Integrations and campaign setup.", "Onboarding: Channels"),
    ("Marketing today", "Campaigns or launches planned in the next 90 days", "Multi-line text", "No", "No", "Pick a first campaign to build live.", "Onboarding note"),
    ("Marketing today", "Who on your team will run HubSpot, and hours per week", "Text", "Yes", "Partly", "Training scope and realistic timeline.", "Onboarding: Team capacity"),
    ("Marketing today", "Other agencies or freelancers involved", "Text", "No", "No", "Avoid overlap; access and handoff.", "Onboarding note"),
    ("Content approval", "Who approves emails/pages before they go live, and how fast?", "Text", "Yes", "No", "Sets UAT turnaround in the plan.", "Onboarding: Approver"),
    ("Tech", "HubSpot hubs and tiers you own", "Checkboxes per hub + tier", "Yes", "Yes (confirm)", "Determines which setup items apply (Starter / Pro / Enterprise).", "Company: Hub tiers"),
    ("Tech", "Website platform and who can edit it", "Dropdown + text", "Yes", "Partly", "Tracking code and embedded forms.", "Company: CMS"),
    ("Tech", "Email domain you send from", "Text", "Yes", "No", "Email sending domain authentication.", "Onboarding: Sending domain"),
    ("Tech", "Other tools we must connect or migrate from", "Multi-line text (CRM, email tool, ads, webinar, chat, analytics)", "Yes", "Partly", "Integration and migration scope.", "Company: Tech stack"),
    ("Tech", "Where do your contacts live today and roughly how many?", "Text + number", "Yes", "No", "Import scope and marketing contact tier.", "Onboarding note"),
    ("Compliance", "Regions you market to and consent rules you follow", "Checkboxes: US, Canada (CASL), EU/UK (GDPR), Other", "Yes", "No", "Subscription types, consent and cookie banner.", "Onboarding: Compliance"),
    ("Compliance", "Industry regulations (e.g. HIPAA, financial)", "Text", "No", "No", "Data handling limits.", "Onboarding: Compliance"),
    ("Brand", "Upload brand guide, logos, fonts, email templates", "File upload", "Yes", "No", "Brand kit and templates.", "Files on onboarding record"),
    ("Access", "Checklist: HubSpot partner access, website admin, GA4/GTM, ad accounts, social accounts", "Checkboxes", "Yes", "Partly", "One list so access isn't chased for weeks.", "Onboarding: Access status"),
]

# area, item, details, tier (S/P/E = Starter/Pro/Enterprise), phase task id, owner
TECH_SETUP = [
    ("Account", "Users, teams & permission sets", "Invite client users, set permissions by role, teams if needed.", "S", "4.01", "Architect"),
    ("Account", "Security", "Require 2FA; SSO on Enterprise.", "S", "4.01", "Architect"),
    ("Account", "Account defaults", "Company info, time zone, currency, fiscal year; brands/business units (Ent).", "S", "4.01", "Architect"),
    ("Tracking", "Install tracking code", "On every domain (CMS plugin or GTM). Verify with a test visit.", "S", "4.02", "Architect"),
    ("Tracking", "Exclude internal traffic", "Client and RevGravy IPs/domains excluded from analytics.", "S", "4.02", "Architect"),
    ("Tracking", "Cookie consent banner", "Configured per regions in intake.", "S", "4.02", "Architect"),
    ("Domains", "Connect content domains", "Landing pages / blog subdomain (e.g. go.client.com).", "S", "4.03", "Architect"),
    ("Domains", "Email sending domain authentication", "SPF, DKIM, DMARC records added by client DNS contact; verified in HubSpot.", "S", "4.03", "Architect + client IT"),
    ("Email", "Subscription types", "Defined per content type; mapped to consent requirements.", "S", "4.04", "Architect"),
    ("Email", "Footer, office address, default sender", "Compliant footer, real sender name.", "S", "4.04", "Architect"),
    ("Email", "Brand kit & email templates", "Logo, colors, fonts; 2–3 reusable templates.", "S", "4.04", "Architect"),
    ("Email", "Double opt-in", "Only if compliance requires it.", "S", "4.04", "Architect"),
    ("Data", "Property audit & custom properties", "Remove unused, add what the Factories need. Naming convention documented.", "S", "4.05", "Architect"),
    ("Data", "Lifecycle stages & lead status", "Definitions agreed with client; automation set.", "S", "4.05", "Architect"),
    ("Data", "Marketing contact rules", "Who is a marketing contact; keeps billing under control.", "S", "4.05", "Architect"),
    ("Data", "Import contacts & companies", "Mapped import, dedupe, associations.", "S", "4.06", "Architect"),
    ("Data", "Data hygiene workflows", "Formatting, required fields, duplicates.", "P", "4.06", "Architect"),
    ("Integrations", "Website CMS / non-HubSpot forms", "Embed or collect external forms.", "S", "4.07", "Architect"),
    ("Integrations", "GA4", "Connect for reporting.", "S", "4.07", "Architect"),
    ("Integrations", "Ad accounts", "Google, Meta, LinkedIn; conversion events.", "S", "4.07", "Architect"),
    ("Integrations", "Social accounts", "Connect for publishing and reporting.", "S", "4.07", "Architect"),
    ("Integrations", "Webinar / Zoom, Slack, other apps", "As listed in intake.", "S", "4.07", "Architect"),
    ("Integrations", "CRM sync (if CRM isn't HubSpot)", "Field mapping, sync rules, lifecycle alignment.", "P", "4.07", "Architect"),
    ("Integrations", "Supered", "Install and grant client users access.", "S", "1.05", "Ops"),
    ("Lead capture", "Forms", "Hidden fields, consent, progressive fields (Pro).", "S", "5.01", "Architect"),
    ("Lead capture", "CTAs / pop-ups", "Per offer.", "S", "5.01", "Architect"),
    ("Lead capture", "Landing & thank-you pages", "Template + first pages.", "S", "5.01", "Architect"),
    ("Lead capture", "Meetings link", "For sales handoff from nurture.", "S", "5.01", "Architect"),
    ("Segmentation", "Core segments", "Persona, lifecycle, engagement, customers, suppression.", "S", "5.02", "Architect"),
    ("Automation", "Nurture workflows", "Per persona / offer.", "P", "5.03", "Architect"),
    ("Automation", "Lead scoring", "Fit + engagement score; MQL threshold.", "P", "5.04", "Architect"),
    ("Automation", "MQL handoff", "Assignment, notifications, SLA tasks.", "P", "5.04", "Architect"),
    ("Campaigns", "Campaigns & UTMs", "Campaign object, UTM conventions, assets associated.", "P", "5.05", "Architect"),
    ("Campaigns", "Ad audiences", "Retargeting and segment-based audiences.", "P", "5.06", "Architect"),
    ("Reporting", "Progress-measure dashboard", "One report per Factory; baseline vs now.", "S", "4.08", "Architect"),
    ("Reporting", "Marketing performance dashboard", "Traffic, leads, MQLs, emails, campaigns.", "S", "5.07", "Architect"),
    ("Reporting", "Attribution reports", "Multi-touch revenue attribution.", "E", "5.07", "Architect"),
    ("AI", "Breeze / AI settings", "Brand voice, content tools, agents — within agreed AI terms.", "S", "5.08", "Architect"),
    ("QA", "End-to-end test", "Visit → form → contact → workflow → email → notification.", "S", "4.09", "Architect"),
    ("QA", "Client sign-off (UAT)", "Client approves each delivery before go-live.", "S", "5.09", "Client POC"),
]

# module, audience, content, format, when (task / day), length
TRAINING = [
    ("T1 · HubSpot basics", "All client users", "Navigation, records, notifications, where to find help.", "Supered tour + video", "After access (≈ Day 7)", "10 min"),
    ("T2 · Contacts & segments", "Marketing team", "Contact records, properties, segments, data hygiene habits.", "Video + office hours practice", "After data import (≈ Day 25)", "20 min"),
    ("T3 · Email marketing", "Marketing team", "Build, test, send and analyze emails using your templates.", "Video + live build in office hours", "After email foundations (≈ Day 20)", "25 min"),
    ("T4 · Forms, landing pages & CTAs", "Marketing team", "Create and edit lead capture assets.", "Video", "After lead capture ships (≈ Day 40)", "20 min"),
    ("T5 · Workflows & nurture", "HubSpot admin(s)", "Read, edit and safely clone workflows.", "Live session", "After nurture ships (≈ Day 55)", "30 min"),
    ("T6 · Campaigns, ads & social", "Marketing team", "Campaign object, UTMs, ads and social reporting.", "Video", "After first campaign (≈ Day 65)", "20 min"),
    ("T7 · Reporting & dashboards", "Marketing lead + leadership", "Read the progress-measure dashboard; build a report.", "Live at MBR #2", "≈ Day 60", "20 min"),
    ("T8 · Lead handoff", "Marketing + sales", "MQL definition, notifications, follow-up SLA.", "Live session", "After MQL handoff ships (≈ Day 60)", "20 min"),
    ("T9 · Admin handbook", "HubSpot admin(s)", "How your portal is built and how to maintain it.", "Supered Base", "≈ Day 85", "Self-serve"),
]

# touchpoint, timing, channel, owner, content
COMMS = [
    ("Welcome email #1", "Day 0", "Email from Phil", "Automation", "Welcome, Supered Action Plan link, kickoff booking link, first to-dos (access + intake)."),
    ("Welcome email #2", "Day 2", "Email", "Automation", "How we work: office hours, weekly updates, requests & urgency classes ($250), escalation path, AI use."),
    ("Access / intake reminders", "Day 3–5 if incomplete", "Email", "Automation", "Friendly reminder with the exact missing items."),
    ("Supered announcement", "Day 2–3", "Supered", "Architect", "How Supered works: Bases, announcements, documentation."),
    ("Kickoff (15 min)", "Day 5–10", "Video call", "Architect", "Intros, plan, missing items, office hours, MBRs."),
    ("Kickoff recap", "Within 24h of kickoff", "Email", "Architect (AI draft)", "Decisions, owners, dates, client to-dos."),
    ("Weekly update", "Every Friday", "Email", "Architect (AI draft)", "1) What we did and which strategic issue it moves  2) KPIs vs baseline  3) Issues found that aren't in scope  4) Next week  5) Your to-dos."),
    ("Delivery announcement", "Each delivery", "Supered video", "Architect", "What was built, how to use it, why it matters."),
    ("Office hours", "Weekly slots", "Booking link", "Architect", "Questions, coaching, training practice."),
    ("MBR", "≈ Day 30 and Day 60", "Video call", "Architect + Phil", "Progress vs benchmark, KPI trend, issues and opportunities."),
    ("What's next", "≈ Day 60–65", "Video call", "Phil + Architect", "Long-term vision, A/B next phase."),
    ("Final results review", "≈ Day 80–88", "Video call", "Architect", "Before vs after, what we built, what's open."),
    ("KPI monitoring", "Monthly for 6 months", "Scheduled dashboard email", "Automation", "Progress measures snapshot."),
]

# criterion, HubSpot Work, Projects object, Tickets — each cell: (score 0-2, note)
TOOL_FIT = [
    ("One record per customer program", (2, "Row in a tracker table linked to the CRM company/deal"), (2, "Native CRM record, associated to deal/company/contacts"), (1, "Possible, but tickets are built for single requests")),
    ("Reusable task template per program", (2, "Project templates; AI builds from a prompt"), (1, "Tasks on records; templates/dependencies maturing — confirm in portal"), (1, "Workflow-created tasks only")),
    ("Timeline / Gantt / due dates", (1, "Dates and statuses in tables"), (2, "Gantt, board, table, calendar views"), (0, "Board only")),
    ("Client can see their plan", (0, "Internal workspace"), (2, "'Visible to Onboarding Customers' → customer portal"), (1, "Customer portal shows tickets")),
    ("Trigger from closed-won deal", (1, "Agents can react to CRM changes (beta)"), (2, "Standard workflows"), (2, "Standard workflows")),
    ("Reporting (health, time in stage)", (1, "Table views"), (2, "Standard reports, time-in-stage props"), (2, "Standard reports")),
    ("Intake forms feed the record", (2, "Work forms create table rows"), (1, "HubSpot form + workflow"), (1, "HubSpot form + workflow")),
    ("Playbooks / docs next to the work", (2, "Work documents"), (0, "Notes/attachments only"), (0, "Notes only")),
    ("AI drafts (handoff, weekly update)", (2, "Built-in agents (uses HubSpot Credits)"), (1, "Breeze / workflow AI actions"), (1, "Breeze / workflow AI actions")),
    ("Client requests & change orders", (1, "Table of requests"), (0, "Not its job"), (2, "Already running: 'Active' ticket pipeline")),
    ("Maturity / risk", (0, "Public beta; features may change"), (2, "Generally available, already used for Factories"), (2, "Generally available")),
]

TOOL_VERDICT = [
    ("HubSpot Work", "The team's operating hub: template library, intake form, onboarding tracker, playbook docs and AI agents (handoff brief, weekly update drafts, delay alerts). Start here as the pilot your boss asked for."),
    ("Projects object", "The customer's onboarding record of truth: one record per program, associated to the deal, with tasks, Gantt, health and customer-portal visibility. Factories (progress measures) already live here."),
    ("Tickets", "Client requests during the program: urgency class, $250 out-of-scope requests, 'not now' ideas. Keep the existing 'Active' pipeline."),
    ("Tasks", "Every to-do has an owner and a due date so it lands on the Architect's queue and calendar (fixes 'Architect needs work scheduled')."),
]

# HubSpot build spec: (area, item, spec)
BUILD_SPEC = [
    ("Projects object", "New pipeline: 'Client Onboarding'", "Stages: Welcome → Access & Intake → Kickoff → Foundations → Build & Launch → Wrap-up & Next Phase → Completed (closed) | Paused | Cancelled (closed)."),
    ("Projects object", "Type (hs_type) value", "'Marketing Hub Onboarding' (later: Sales Hub Onboarding, Sales Team Onboarding)."),
    ("Projects object", "Reuse existing props", "Onboarding plan customer goal, Success metrics, Risks and blockers, Status (health), Start date, Target due date, Canvas / FigJam Link, Visible to Onboarding Customers."),
    ("Projects object", "New props", "Architect, Kickoff date, Next MBR date, Supered Action Plan URL, Office hours link, Hub tier, Sending domain, DNS contact, Access status, Last weekly update sent."),
    ("Projects object", "Naming", "'<Client> · Marketing Hub Onboarding' so it never mixes up with '<Client> 1.1 … to …' Factory records."),
    ("Projects object", "Task template", "Tasks from the Task Template tab, with due dates offset from Start date."),
    ("Deals", "Required props on 'Start Payment Received'", "Canvas / FigJam Link, From→To statement, line items, POC contact, AI terms confirmed, escalation path."),
    ("Workflow", "WF-01 Closed-won → onboarding", "Create onboarding project, associate deal/company/contacts, copy props, create Phil handoff task, notify Slack, enroll POC in welcome emails."),
    ("Workflow", "WF-02 Access & intake reminders", "If access or intake not done by Day 3 / Day 4, send reminder and create task for Architect."),
    ("Workflow", "WF-03 Weekly update task", "Every Thursday while stage is open: task 'Review & send weekly update' + AI draft."),
    ("Workflow", "WF-04 Health alert", "Status → At risk/Off track: notify Phil, create task."),
    ("Workflow", "WF-05 Day 55 'what's next' prep", "Create prep task for Phil and Architect."),
    ("Workflow", "WF-06 Close-out", "Stage → Completed: feedback survey, start KPI monitoring, create 90-day check-in task."),
    ("Tickets", "Active pipeline: new props", "Urgency class, In scope? (In scope / Out of scope – quote / Not now), Price ($250 default for new requests)."),
    ("Tickets", "Optional 'Not Now' pipeline", "Ideas and issues to sell later; feeds the 'what's next' call."),
    ("HubSpot Work", "Workspace: 'Client Onboarding'", "Project: 'Marketing Hub Onboarding'. Tables: Onboarding Tracker, Task Template Library, Tech Setup Checklist, Intake Responses, Issues & Not-Now Ideas, Weekly Update Log, Training Tracker."),
    ("HubSpot Work", "Forms", "Client Intake Form (→ Intake Responses), Sales→Architect Handoff Form, New Request Form."),
    ("HubSpot Work", "Documents", "Onboarding Playbook, Kickoff Agenda, Weekly Update Template, MBR Template, 'What's Next' Script, Welcome Email Copy."),
    ("HubSpot Work", "Agents", "Handoff Brief (on new tracker row), Weekly Update Drafter (Thursdays), Delay Flagger (daily), Not-Now Collector."),
]

OPEN_QUESTIONS = [
    ("Program", "Which Marketing Hub tiers do we sell onboarding for (Starter, Pro, Enterprise)? Is there one package or several?", "Which Tech Setup items are in scope"),
    ("Roles", "Is Phil always the strategy lead, or will other people sell and hand off too?", "Owner column, handoff workflow"),
    ("Roles", "How is the Architect picked: Phil chooses, or rotation by capacity?", "WF-01 assignment"),
    ("Tools", "Is the portal enrolled in the HubSpot Work beta yet, and who is Super Admin?", "Whether we can build in Work now"),
    ("Tools", "OK to add a 'Client Onboarding' pipeline to the Projects object (the one renamed 'Factory'), or keep onboarding only in HubSpot Work?", "Record of truth"),
    ("Tools", "Will customers use the HubSpot customer portal, or is Supered the only client-facing place?", "'Visible to Onboarding Customers' setting"),
    ("Delivery", "What are the standard Factories (progress measures) for a Marketing Hub program? E.g. 1.1 Visitor → Lead, 1.2 Lead → MQL, 2.1 MQL → Meeting.", "Delivery Template + Build phase"),
    ("Delivery", "Is the $250 new-request price per request, and what are the urgency classes?", "Ticket properties"),
    ("Delivery", "Are migrations (e.g. Mailchimp → HubSpot) and website work in scope, or separate products?", "Scope of Foundations"),
    ("Commercial", "What exactly do the post-program offers cost and include?", "Phase 9 offers"),
]
