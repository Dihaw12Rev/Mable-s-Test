"""Single source of truth for the RevGravy Marketing Hub Onboarding process (v2).

build_workbook.py (the sheet), build_roadmap.py (the visual roadmap) and
build_prompt.py (the HubSpot Work prompt) all read from this file, so edit the
process here and re-run all three.

Day offsets are counted from Day 0 = deal reaches "Start Payment Received"
(the closed-won stage of the Sales Pipeline). The plan is laid out for the
longest program (90 days). Customers on a shorter program (60–90 days) get
their later due dates compressed with scaled_due().
"""

PROGRAM_DAYS = 90        # the plan below is laid out for this length
PROGRAM_MIN_DAYS = 60    # shortest program we sell
FIXED_UNTIL_DAY = 10     # week-one tasks (welcome, access, kickoff) never compress


def scaled_due(phase, due, program_days):
    """Due day for a customer whose program is program_days long."""
    if phase == "P0" or due <= FIXED_UNTIL_DAY:
        return due
    if phase == "P9":                       # post-program: counted from the program's end
        return due - PROGRAM_DAYS + program_days
    return int(due * program_days / PROGRAM_DAYS + 0.5)   # half-up, same as Excel ROUND


ROLES = {
    "Phil": "Strategy lead through the sale and the handoff. Picks the Architect based on capacity. Reviews next-phase options.",
    "Architect": "Takes over as strategy lead after the handoff. Owns delivery, weekly updates, office hours, MBRs and the 'what's next' call.",
    "Ops": "RevGravy operations. Owns the templates, Supered setup and the welcome emails.",
    "Client POC": "Main point of contact at the customer. Owns approvals, access and client to-dos.",
}

# Answers from the review (Oct 2026). question, answer, what changed
DECISIONS = [
    ("Program length", "60 to 90 days.", "The plan is laid out for 90 days. Each customer has a Program length on their Customers row; later due dates compress to fit 60 or 75 days."),
    ("Hub tiers", "Marketing Hub Professional and Enterprise.", "Starter removed. Setup items are tagged 'Pro & Ent' or 'Ent only'."),
    ("Strategy lead", "Phil leads through the sale, then the Architect takes over.", "Architect owns MBRs, weekly updates, strategy and the 'what's next' call after the handoff. Phil reviews the next-phase options."),
    ("Picking the Architect", "Phil decides, based on capacity.", "Capacity report in the Onboarding Portfolio (active customers per Architect)."),
    ("HubSpot Work beta", "Enrolled.", "Build in HubSpot Work now."),
    ("Where onboarding lives", "Only in HubSpot Work.", "No Projects pipeline and no tickets for onboarding. Tasks, board and requests all live in Work."),
    ("Client-facing place", "Supered.", "No HubSpot customer portal. Everything the customer sees is in Supered."),
    ("Progress measures (Factories)", "Use the suggestion.", "Marketing Hub: 0.1, 1.1, 1.2, 1.3, plus 1.0 and 1.4 when bought. Sales Hub: 2.1, 2.2, 3.2, plus 3.1. Service Hub: 4.1, 4.2, plus 4.3."),
    ("$250 requests", "Per request. Urgency classes not defined yet.", "Recommended classes added: Critical, High, Standard, Not now."),
    ("Migrations & website work", "In scope.", "Migration and website tasks added to Foundations and Build & launch, with suggested limits."),
    ("Post-program offers", "Free for 6 months. Contents not defined yet.", "Suggested contents for the free KPI monitoring and the three paid offers."),
    ("'What's next' call", "The Architect runs it.", "Tasks 8.02, 8.03 and 9.04 owned by the Architect; Phil reviews the options in 8.01."),
    ("Suggestions from review", "Approved: urgency classes, 2-hour request size, migration and website limits, standard progress measures, $1,670/mo Monthly Plan for team support.", "Applied as written."),
    ("Agents", "HubSpot Work can build agents.", "8 agents added. They only draft, fill dates or flag; none sends anything to a customer."),
    ("Agent schedules", "Bogotá time.", "Every scheduled agent runs on America/Bogota time."),
    ("Creating a customer's tasks", "Products purchased + a Create tasks checkbox.", "Ops picks the products and ticks Create tasks. The Task Generator agent copies the Core tasks once plus one module per hub, and records which hubs are done in Tasks created for."),
    ("Task library", "Marketing, Sales and Service Hub onboarding.", "One Task Library: Core tasks every customer gets (58) plus a module per hub: Marketing Hub (MH-, 16), Sales Hub (SH-, 14), Service Hub (SV-, 11)."),
    ("Day 0", "The day the deal reaches Start Payment Received.", "Not the kickoff date. Kickoff happens on Days 5–10."),
    ("Update statuses", "Draft, Reviewed, Sent.", "An agent writes Draft; the Architect sets Reviewed, and Sent once it goes to the customer."),
    ("Request handling", "Owner column, USD, reply times.", "Each request has an Owner (default: the customer's Architect). Price is USD. High and Standard get a reply within 1 business day."),
    ("HubSpot Work limits (found in the build)", "No custom project fields; copies of a project don't carry agent workflows.", "All customers share the Customer Task, Request and Update tables, each row linked to its Customers row. The template project's Tasks table is the master list the Task Generator copies from."),
]

PHASES = [
    {"id": "P0", "name": "Handoff checklist", "start": -30, "end": 0,
     "figjam": "New Lead → VSL → Fit/Discovery → Assess Tech Stack → Video → Recommendation → Closing Call",
     "goal": "Everything the Architect needs is on the deal before the customer pays (Definition of Ready).",
     "client_sees": "VSL, recommendation video, proposal Q&A, quote, agreement.",
     "exit": "Deal has FigJam link, From→To statement, products, progress measures, survey, POC and supporters, signed agreement."},
    {"id": "P1", "name": "Close & welcome", "start": 0, "end": 3,
     "figjam": "Paid & Agreement Signed",
     "goal": "The customer feels the handoff right away; the Architect is picked and briefed within 72 hours.",
     "client_sees": "Welcome email series with the Supered Action Plan (expectations, next steps, links, agreement, to-dos).",
     "exit": "Architect assigned, Phil↔Architect 1:1 done, customer added in HubSpot Work with tasks created, kickoff booked."},
    {"id": "P2", "name": "Access & intake", "start": 1, "end": 7,
     "figjam": "HS Access / Form / Trello",
     "goal": "Every access and input we need arrives in week 1. No Trello.",
     "client_sees": "Supered announcement on how we deliver updates and documentation; one short intake form.",
     "exit": "Portal access granted, intake submitted, audit and baseline numbers captured."},
    {"id": "P3", "name": "Kickoff", "start": 5, "end": 10,
     "figjam": "Kickoff Session 15 min",
     "goal": "15 minutes that confirm the plan, close gaps and set the rhythm.",
     "client_sees": "Architect + team intro, confirmed plan, office hours and MBRs explained and booked.",
     "exit": "Plan confirmed, missing items owned, MBRs on calendars, recap sent within 24h."},
    {"id": "P4", "name": "Foundations", "start": 7, "end": 30,
     "figjam": "Delivery Template → technical setup",
     "goal": "Marketing Hub set up correctly: tracking, domains, email, data, migration, website connection, baseline dashboard.",
     "client_sees": "Supered video announcements as foundation items finish; weekly updates.",
     "exit": "Foundation QA passed, old data migrated, baseline dashboard live."},
    {"id": "P5", "name": "Build & launch", "start": 21, "end": 75,
     "figjam": "Tactical outcomes / Factories (progress measures)",
     "goal": "Build each progress measure the customer bought and get it live.",
     "client_sees": "A Supered video per delivery, sign-off requests, numbers moving in weekly updates.",
     "exit": "Every progress measure is live, approved by the client and reporting."},
    {"id": "P6", "name": "Training & adoption", "start": 14, "end": 85,
     "figjam": "Office Hours / Supered videos",
     "goal": "The customer's team can run what we built without us.",
     "client_sees": "Short Supered training videos, office-hours coaching, an admin handbook.",
     "exit": "Each audience finished its modules; adoption checks passed."},
    {"id": "P7", "name": "Run cadence", "start": 7, "end": 90,
     "figjam": "Office Hours + Weekly updates",
     "goal": "Same rhythm every week: office hours, Friday update, monthly business review, requests handled by urgency.",
     "client_sees": "Weekly update (work done → strategic issue, numbers, issues found), office hours, MBRs.",
     "exit": "Runs every week until the program ends."},
    {"id": "P8", "name": "What's next", "start": 60, "end": 90,
     "figjam": "30 Days Before We Finish, Explain What's Next",
     "goal": "The customer sees the long-term vision and picks the next phase before the program ends.",
     "client_sees": "'What's next' call with the Architect, A/B options, final results review.",
     "exit": "Next phase chosen (A, B or KPI monitoring only), results reviewed, project closed."},
    {"id": "P9", "name": "After the program", "start": 90, "end": 270,
     "figjam": "Post-1st Program Offers + Goal: keep relationship 6–12 months",
     "goal": "Keep the relationship for 6–12 more months, starting with 6 months of free KPI monitoring.",
     "client_sees": "Monthly KPI snapshot, check-ins at month 3 and 6, paid offers.",
     "exit": "Customer moved to a paid offer, or monitoring ends cleanly after 6 months."},
]

# Columns: id, phase, task, definition of done, owner, client_facing, start_day, due_day,
#          depends_on, lives_in, repeats
TASKS = [
    # P0 — Handoff checklist (done before Day 0, verified at the Phil ↔ Architect handoff)
    ("0.01", "P0", "Research brief from company URL", "Website URL on the deal; research brief attached as a note before the Fit call.", "Phil", "No", -30, -28, "", "Deal note", ""),
    ("0.02", "P0", "FigJam canvas after Fit call", "Covers strategic motivation, tactical outcomes, progress measures and fee range. Link saved on the deal.", "Phil", "No", -25, -21, "0.01", "Deal: Canvas / FigJam Link", ""),
    ("0.03", "P0", "From→To statement captured", "One sentence: from where they are today to where they want to be. Every weekly update ties back to it.", "Phil", "No", -25, -21, "0.02", "Deal property", ""),
    ("0.04", "P0", "Tech stack & team capacity survey", "Client gave HubSpot access and finished the survey: tools beyond HubSpot, internal processes and cadences, current KPIs.", "Client POC", "Yes", -21, -14, "0.02", "Form → deal/company", ""),
    ("0.05", "P0", "Products and quote on the deal", "Pricing calculator used, line items added, quote created. Each hub bought is Pro or Enterprise.", "Phil", "No", -14, -10, "0.04", "Deal line items + quote", ""),
    ("0.06", "P0", "Progress measures picked", "The standard progress measures for each hub bought (Progress Measures tab), plus any optional ones. Baselines noted if known.", "Phil", "No", -14, -7, "0.05", "Deal note", ""),
    ("0.07", "P0", "POC and supporters identified", "Contacts on the deal with labels (POC, Supporter, Billing, Decision maker). POC gets the weekly email.", "Phil", "Yes", -10, -3, "0.05", "Deal contacts", ""),
    ("0.08", "P0", "Agreement signed", "Includes AI terms, escalation path, how progress is measured, POC and supporters, strategic job → tactical outcomes → progress measures, and request handling ($250 per request, urgency classes).", "Client POC", "Yes", -5, 0, "0.07", "Quote / e-signature", ""),

    # P1 — Close & welcome
    ("1.01", "P1", "Pick the Architect", "Phil checks the Capacity report (active customers per Architect) and picks the Architect.", "Phil", "No", 0, 1, "0.08", "Work: Capacity report", ""),
    ("1.02", "P1", "Add the customer in HubSpot Work", "Add a Customers row: Customer, Company, Deal, Architect, Program length, Start date (the payment date), Products purchased, hub tiers, From→To goal, FigJam and Supered links. Tick Create tasks and check the Task Generator filled Tasks created for.", "Ops", "No", 0, 1, "1.01", "Work: Customers table", ""),
    ("1.03", "P1", "Welcome email #1: welcome + Action Plan", "Sent from Phil on Day 0: Supered Action Plan link, kickoff booking link, first to-dos (grant HubSpot access, fill the intake form).", "Ops", "Yes", 0, 0, "0.08", "HubSpot email (automated on deal stage)", ""),
    ("1.04", "P1", "Build the Supered Action Plan", "Duplicate the Action Plan template for the products bought; add the agreement, FigJam, client to-dos and access checklist.", "Ops", "Yes", 0, 1, "1.02", "Supered", ""),
    ("1.05", "P1", "Phil ↔ Architect handoff (30 min)", "Walk through FigJam, customer context, products, the From→To goal, progress measures and KPIs, schedule. Architect checks the Handoff checklist section. Strategy lead moves to the Architect after this call.", "Phil", "No", 1, 3, "1.01", "Meeting on the deal", ""),
    ("1.06", "P1", "Set up progress measures", "Add the customer's progress measures to their Customers row (name '<Client> 1.1 Visitor to Lead' etc.) with baseline, target and schedule.", "Architect", "No", 1, 3, "1.05", "Work: Customers row", ""),
    ("1.07", "P1", "Office hours booking link", "Architect's HubSpot meetings link (office-hours type) added to the Supered plan.", "Architect", "Yes", 1, 2, "1.01", "HubSpot Meetings + Supered", ""),
    ("1.08", "P1", "Welcome email #2: how we work", "Day 2: office hours, Friday updates, how to send a request and the urgency classes, escalation path, how we use AI.", "Ops", "Yes", 2, 2, "1.03", "HubSpot email (automated)", ""),
    ("1.09", "P1", "Kickoff booked", "Client books the 15-minute kickoff from welcome email #1. Chase on Day 3 if not booked.", "Client POC", "Yes", 0, 5, "1.03", "HubSpot Meetings", ""),

    # P2 — Access & intake
    ("2.01", "P2", "HubSpot access granted", "Partner access or a Super Admin user for the Architect. Confirm Pro or Enterprise per hub.", "Client POC", "Yes", 1, 3, "1.03", "Supered to-do", ""),
    ("2.02", "P2", "Intake form submitted", "Short form with only what pre-sale didn't capture (Intake Form tab).", "Client POC", "Yes", 1, 5, "1.03", "Intake form", ""),
    ("2.03", "P2", "Access to connected systems", "DNS/IT contact, website CMS, GA4/GTM, ad and social accounts, and every old tool we migrate from (email tool, CRM, help desk).", "Client POC", "Yes", 1, 7, "2.02", "Supered to-do", ""),
    ("2.04", "P2", "Brand & content assets shared", "Brand guide, logos, fonts, colors, email templates, key content, lists to import.", "Client POC", "Yes", 1, 7, "2.02", "Supered upload", ""),
    ("2.05", "P2", "Supered announcement to POC", "Short video: how Supered works (Bases, announcements, documentation) and where updates show up.", "Architect", "Yes", 2, 3, "1.04", "Supered", ""),
    ("2.06", "P2", "Portal audit", "Data health, email health, existing assets, tracking, workflows, properties, old tool inventory. 1-page summary for kickoff.", "Architect", "No", 3, 7, "2.01", "Work: Update table", ""),
    ("2.07", "P2", "Baseline numbers", "Record the 'before' number for each progress measure.", "Architect", "No", 5, 7, "2.06", "Work: Customers row", ""),

    # P3 — Kickoff
    ("3.01", "P3", "Kickoff agenda", "Plan summary, missing items, decisions needed. Drafted from intake + audit.", "Architect", "No", 5, 7, "2.02, 2.06", "Work: Update table", ""),
    ("3.02", "P3", "Kickoff session (15 min)", "Architect & team intro; confirm the goal and plan; walk through missing items; explain office hours, Friday updates, MBRs and how to send requests.", "Architect", "Yes", 5, 10, "3.01", "Meeting", ""),
    ("3.03", "P3", "Book MBRs and the 'what's next' call", "MBR #1 ≈ Day 30, MBR #2 ≈ Day 60, 'what's next' ≈ Day 60–65, final results review ≈ Day 85 (scaled to program length).", "Architect", "Yes", 5, 10, "3.02", "Meetings", ""),
    ("3.04", "P3", "Kickoff recap within 24h", "Decisions, owners, dates, client to-dos. Supered plan updated.", "Architect", "Yes", 6, 11, "3.02", "Email + Supered", ""),

    # P4 — Foundations
    ("4.01", "P4", "Account, users & security", "Users, permission sets, 2FA; Enterprise extras where bought.", "Architect", "No", 7, 12, "2.01", "Tech Setup tab", ""),
    ("MH-4.02", "P4", "Tracking & consent", "Tracking code on every domain, internal traffic excluded, cookie banner set.", "Architect", "No", 7, 14, "2.03", "Tech Setup tab", ""),
    ("MH-4.03", "P4", "Domains & email authentication", "Content domain connected; sending domain authenticated (SPF, DKIM, DMARC) with the client's DNS contact.", "Architect", "No", 7, 18, "2.03", "Tech Setup tab", ""),
    ("MH-4.04", "P4", "Email foundations", "Subscription types, footer and address, brand kit, email templates, default sender.", "Architect", "No", 10, 18, "2.04", "Tech Setup tab", ""),
    ("4.05", "P4", "Data model", "Property audit, lifecycle stage definitions, lead status, marketing-contact rules.", "Architect", "No", 10, 21, "2.06", "Tech Setup tab", ""),
    ("MH-4.06", "P4", "Migration plan & export", "Inventory and export from the old tool: lists, consent, unsubscribes and bounces, templates, active automations.", "Architect", "No", 8, 16, "2.03", "Tech Setup tab", ""),
    ("4.07", "P4", "Data import & cleanup", "Import contacts and companies (including migrated data, with consent mapped and unsubscribes suppressed), dedupe, associations, marketing contacts.", "Architect", "No", 14, 25, "4.05", "Tech Setup tab", ""),
    ("MH-4.08", "P4", "Website connection", "HubSpot forms, CTAs, chat and meetings on the current website; landing page and blog templates.", "Architect", "No", 14, 28, "MH-4.02", "Tech Setup tab", ""),
    ("4.09", "P4", "Integrations", "Every integration the intake lists: GA4, ad and social accounts, webinar tool, Slack, CRM sync if their CRM isn't HubSpot. Mark the ones this customer doesn't need as not applicable.", "Architect", "No", 14, 28, "2.03", "Tech Setup tab", ""),
    ("4.10", "P4", "Baseline dashboard", "One report per progress measure, showing baseline vs now. Used in every weekly update.", "Architect", "Yes", 18, 28, "2.07", "HubSpot dashboard", ""),
    ("4.11", "P4", "Foundation QA", "Test the main flow end to end for each hub bought (Marketing: visit → form → contact → email; Sales: lead → owner → deal; Service: email → ticket → reply).", "Architect", "No", 25, 30, "4.07 and each hub's foundation tasks", "Tech Setup tab", ""),
    ("4.12", "P4", "Supered video: foundations done", "What changed for the customer and why it matters.", "Architect", "Yes", 28, 30, "4.11", "Supered", ""),

    # P5 — Build & launch (one task per progress measure + launch tasks)
    ("MH-5.01", "P5", "Build 1.1 Visitor → Lead", "Forms, CTAs, landing and thank-you pages live on the right pages. Measure: visit-to-contact rate.", "Architect", "No", 21, 40, "MH-4.08, 4.11", "Progress measure 1.1", ""),
    ("MH-5.02", "P5", "Build 1.2 Lead → MQL", "Segments, nurture emails and workflows, lead scoring, lifecycle automation. Client approves copy. Measure: lead-to-MQL rate.", "Architect", "Yes", 30, 55, "MH-5.01, 4.07", "Progress measure 1.2", ""),
    ("MH-5.03", "P5", "Build 1.3 MQL → Meeting", "MQL definition agreed with sales, owner assignment, notifications, follow-up SLA, meetings link in nurture. Measure: MQL-to-meeting rate.", "Architect", "Yes", 35, 60, "MH-5.02", "Progress measure 1.3", ""),
    ("MH-5.04", "P5", "Build 1.4 Subscriber → Engaged (if bought)", "Newsletter or content program, subscription preferences, re-engagement and sunset flows. Measure: email click rate, engaged contacts.", "Architect", "No", 35, 60, "MH-4.04", "Progress measure 1.4", ""),
    ("MH-5.05", "P5", "Build 1.0 Stranger → Visitor (if bought)", "Campaigns and UTMs, ad audiences and conversion events, social publishing, SEO recommendations. Measure: sessions by source.", "Architect", "No", 30, 60, "4.09", "Progress measure 1.0", ""),
    ("MH-5.06", "P5", "Migration: rebuild and switch off old tool", "Rebuild templates and active automations from the old tool, send in parallel once, then switch the old tool off.", "Architect", "Yes", 25, 50, "MH-4.06, 4.07", "Tech Setup tab", ""),
    ("MH-5.07", "P5", "Website: landing pages & blog", "Migrate landing pages and blog posts within the agreed limit; redirects set.", "Architect", "Yes", 30, 60, "MH-4.08", "Tech Setup tab", ""),
    ("MH-5.08", "P5", "First campaign live", "Campaign with UTMs and assets, launched with the client.", "Architect", "Yes", 40, 65, "MH-5.01, MH-5.02", "HubSpot campaigns", ""),
    ("MH-5.09", "P5", "Performance reporting", "Marketing performance dashboard and funnel by progress measure; revenue attribution on Enterprise.", "Architect", "Yes", 45, 70, "4.10", "HubSpot dashboard", ""),
    ("MH-5.10", "P5", "AI / Breeze setup", "Brand voice and content tools, only within the AI terms in the agreement.", "Architect", "No", 45, 70, "MH-4.04", "Tech Setup tab", ""),
    ("5.11", "P5", "Client sign-off per progress measure", "Client approves each build before it goes live.", "Client POC", "Yes", 35, 75, "Each hub's build tasks", "Work: Status 'In review'", ""),
    ("5.12", "P5", "Supered video per delivery", "What was built, how to use it, why it matters.", "Architect", "Yes", 35, 75, "5.11", "Supered", "After each delivery"),

    # P6 — Training & adoption
    ("6.01", "P6", "Confirm training plan", "Who needs which modules (Training tab), from the intake.", "Architect", "Yes", 10, 14, "2.02", "Training tab", ""),
    ("MH-6.02", "P6", "Deliver Marketing Hub training", "Modules T1–T9 as Supered videos + practice in office hours, timed to when each feature ships.", "Architect", "Yes", 14, 85, "6.01", "Supered + office hours", ""),
    ("6.03", "P6", "Adoption check #1", "Logins, emails sent, workflows active, dashboards viewed. Flag low adoption in the weekly update.", "Architect", "No", 45, 45, "6.01", "Work: Customers row", ""),
    ("6.04", "P6", "Admin handbook (Supered Base)", "How the portal is set up: naming, properties, workflows, who owns what.", "Architect", "Yes", 60, 85, "5.11", "Supered Base", ""),
    ("6.05", "P6", "Adoption check #2", "Same check before the final results review.", "Architect", "No", 75, 75, "6.03", "Work: Customers row", ""),

    # P7 — Run cadence (recurring)
    ("7.01", "P7", "Office hours", "Bookable slots for questions, coaching and training practice.", "Architect", "Yes", 7, 90, "1.07", "HubSpot Meetings", "Weekly"),
    ("7.02", "P7", "Weekly update", "Drafted with AI, reviewed and sent by the Architect: work done and the strategic issue it moves, numbers vs baseline, issues found outside scope, next week, client to-dos.", "Architect", "Yes", 7, 90, "4.10", "Email, logged on the deal", "Weekly (Friday)"),
    ("7.03", "P7", "Handle requests by urgency", "Every request gets logged with an urgency class and handled in that time ($250 per request; see Request Classes).", "Architect", "Yes", 7, 90, "", "Work: Request table", "As they come in"),
    ("7.04", "P7", "Log issues and 'not now' ideas", "Out-of-scope issues and client ideas go to the Request table as 'Not now', to sell later.", "Architect", "No", 7, 90, "", "Work: Request table", "As they come in"),
    ("7.05", "P7", "Health check", "Set Health (On track / At risk / Off track) and blockers. Escalate per the escalation path.", "Architect", "No", 7, 90, "", "Work: Customers row (Health)", "Weekly"),
    ("7.06", "P7", "Monthly Business Review", "Progress vs baseline, numbers trend, issues and opportunities. Architect leads; Phil optional.", "Architect", "Yes", 30, 60, "3.03", "Meeting", "Monthly"),
    ("7.07", "P7", "Internal delivery review", "Phil + Architects: at-risk customers, capacity, blockers.", "Phil", "No", 7, 90, "", "Work: Portfolio", "Weekly"),

    # P8 — What's next
    ("8.01", "P8", "Prep next-phase options", "Results so far, issues found and 'not now' list → Option A and Option B. Phil reviews before the call.", "Architect", "No", 55, 60, "7.04", "Work: Update table", ""),
    ("8.02", "P8", "'What's next' call", "Architect explains the long-term vision and the next phase as an A/B choice.", "Architect", "Yes", 60, 65, "8.01", "Meeting", ""),
    ("8.03", "P8", "Next-phase proposal", "New deal in the Sales Pipeline for the chosen offer.", "Architect", "Yes", 62, 70, "8.02", "Deal", ""),
    ("8.04", "P8", "Final results review", "Before vs after for every progress measure, what we built, what's still open.", "Architect", "Yes", 80, 88, "5.11", "Meeting + dashboard", ""),
    ("8.05", "P8", "Close the program", "Supered plan archived, project marked Completed, feedback and testimonial asked for.", "Architect", "Yes", 85, 90, "8.04", "Work + Supered", ""),

    # P9 — After the program (6 months of free KPI monitoring)
    ("9.01", "P9", "Monthly KPI snapshot", "Progress-measure dashboard emailed with 3 short notes from the Architect.", "Architect", "Yes", 90, 270, "8.05", "Scheduled dashboard email", "Monthly × 6"),
    ("9.02", "P9", "Portal health alerts", "Watch for deliverability drops, workflow errors, form submissions down 30%+. Tell the client when one fires.", "Architect", "Yes", 90, 270, "8.05", "HubSpot alerts", "Ongoing"),
    ("9.03", "P9", "Check-in call: month 3", "30 minutes: numbers, what's working, what's next.", "Architect", "Yes", 180, 180, "9.01", "Meeting", ""),
    ("9.04", "P9", "Paid offer conversation: month 5", "Present team support, internal capacity and one-initiative-a-month before monitoring ends.", "Architect", "Yes", 240, 240, "9.03", "Deal", ""),
    ("9.05", "P9", "Check-in call: month 6", "Final monitoring check-in; confirm the paid offer or close monitoring.", "Architect", "Yes", 270, 270, "9.04", "Meeting", ""),

    # ---- Sales Hub module (SH-) ----
    ("SH-4.01", "P4", "Sales users, seats & inboxes", "Sales Hub seats assigned, teams and permission sets set, every rep's inbox and calendar connected, email tracking and logging on.", "Architect", "No", 7, 12, "2.01", "Tech Setup tab", ""),
    ("SH-4.02", "P4", "Deal pipelines & stages", "One pipeline per sales motion. Each stage has exit criteria, a probability and required properties, agreed with the sales lead.", "Architect", "Yes", 8, 18, "2.06", "Tech Setup tab", ""),
    ("SH-4.03", "P4", "Lead management & assignment", "Lead status and lifecycle definitions agreed with marketing, assignment rules (rotation or territory), follow-up SLA.", "Architect", "Yes", 10, 21, "4.05", "Tech Setup tab", ""),
    ("SH-4.04", "P4", "Products, quotes & e-signature", "Product library, quote templates, e-signature, payments if they use them.", "Architect", "No", 14, 25, "SH-4.02", "Tech Setup tab", ""),
    ("SH-4.05", "P4", "CRM migration", "Companies, contacts, open deals, owners and activity history moved from the old CRM or spreadsheets, using a field map the client approved.", "Architect", "Yes", 10, 25, "2.03", "Tech Setup tab", ""),
    ("SH-4.06", "P4", "Sales integrations", "Calling, Zoom or Teams, LinkedIn Sales Navigator, accounting or ERP if needed.", "Architect", "No", 14, 28, "2.03", "Tech Setup tab", ""),
    ("SH-5.01", "P5", "Build 2.1 Lead → Contacted", "Lead rotation, task queues, a first-touch sequence and new-lead notifications. Measure: share of leads contacted within 24 hours.", "Architect", "Yes", 21, 40, "SH-4.03, 4.11", "Progress measure 2.1", ""),
    ("SH-5.02", "P5", "Build 2.2 Meeting → Qualified deal", "Meetings links per rep, qualification properties, deal creation from meetings, call playbooks. Measure: meeting-to-deal rate.", "Architect", "Yes", 28, 50, "SH-5.01", "Progress measure 2.2", ""),
    ("SH-5.03", "P5", "Build 3.1 Deal → Proposal sent (if bought)", "Stage-based tasks and reminders, deal workflows, quote steps in the pipeline. Measure: stage conversion and days in stage.", "Architect", "No", 35, 55, "SH-4.02", "Progress measure 3.1", ""),
    ("SH-5.04", "P5", "Build 3.2 Proposal → Closed won", "Quotes and e-signature in the flow, a closed-won handoff workflow, closed-lost reasons. Measure: win rate and sales cycle length.", "Architect", "Yes", 35, 60, "SH-4.04", "Progress measure 3.2", ""),
    ("SH-5.05", "P5", "Templates, snippets & sequences", "Email templates, snippets and sequences per persona and stage, approved by the sales lead.", "Architect", "Yes", 30, 55, "SH-5.01", "Tech Setup tab", ""),
    ("SH-5.06", "P5", "Sales reporting & forecasting", "Pipeline dashboard, forecast, goals or quotas, rep activity report.", "Architect", "Yes", 45, 70, "4.10", "HubSpot dashboard", ""),
    ("SH-5.07", "P5", "AI / Breeze for sales", "Prospecting and deal tools, only within the AI terms in the agreement.", "Architect", "No", 45, 70, "SH-4.01", "Tech Setup tab", ""),
    ("SH-6.02", "P6", "Deliver Sales Hub training", "Modules S1–S5 as Supered videos + practice in office hours, timed to when each feature ships.", "Architect", "Yes", 14, 85, "6.01", "Supered + office hours", ""),

    # ---- Service Hub module (SV-) ----
    ("SV-4.01", "P4", "Service users, seats & help desk", "Service Hub seats, teams and permission sets, the help desk workspace and business hours.", "Architect", "No", 7, 12, "2.01", "Tech Setup tab", ""),
    ("SV-4.02", "P4", "Support channels", "Support email, chat, forms and calling connected to the help desk, plus WhatsApp or Messenger if used.", "Architect", "Yes", 8, 18, "2.03", "Tech Setup tab", ""),
    ("SV-4.03", "P4", "Ticket pipelines & routing", "Ticket pipelines and stages, priority and category properties, required fields, routing rules.", "Architect", "Yes", 10, 21, "SV-4.01", "Tech Setup tab", ""),
    ("SV-4.04", "P4", "Help desk migration", "Open tickets, ticket history, knowledge base articles and saved replies moved from the old help desk.", "Architect", "Yes", 10, 25, "2.03", "Tech Setup tab", ""),
    ("SV-4.05", "P4", "SLAs & escalation", "First-response and time-to-close SLAs by priority, escalation rules, business hours.", "Architect", "Yes", 14, 25, "SV-4.03", "Tech Setup tab", ""),
    ("SV-5.01", "P5", "Build 4.1 Ticket → Resolved", "Routing, SLA alerts, ticket automation, snippets and templates, escalation workflows. Measure: time to first response and time to close.", "Architect", "Yes", 21, 45, "SV-4.05, 4.11", "Progress measure 4.1", ""),
    ("SV-5.02", "P5", "Build 4.2 Question → Self-served", "Knowledge base structure and the top 20 articles, customer portal if bought, AI chat within the AI terms. Measure: knowledge base views vs new tickets.", "Architect", "Yes", 30, 60, "SV-4.04", "Progress measure 4.2", ""),
    ("SV-5.03", "P5", "Build 4.3 Customer → Renewed (if bought)", "CSAT or NPS surveys, customer success workspace, health scores, renewal reminders. Measure: survey response, health score and renewal rate.", "Architect", "Yes", 35, 65, "SV-4.01", "Progress measure 4.3", ""),
    ("SV-5.04", "P5", "Service reporting", "Help desk dashboard, SLA report, agent performance, CSAT trend.", "Architect", "Yes", 45, 70, "4.10", "HubSpot dashboard", ""),
    ("SV-5.05", "P5", "AI / Breeze for service", "Customer agent and help desk AI tools, only within the AI terms in the agreement.", "Architect", "No", 45, 70, "SV-5.02", "Tech Setup tab", ""),
    ("SV-6.02", "P6", "Deliver Service Hub training", "Modules V1–V5 as Supered videos + practice in office hours, timed to when each feature ships.", "Architect", "Yes", 14, 85, "6.01", "Supered + office hours", ""),
]

MODULES = {"Core": "Every customer", "MH": "Marketing Hub", "SH": "Sales Hub", "SV": "Service Hub"}
PRODUCTS = {"MH": "Marketing Hub Onboarding", "SH": "Sales Hub Onboarding", "SV": "Service Hub Onboarding"}


def module_of(task_id):
    """'MH-4.03' -> 'MH'; '4.07' -> 'Core'."""
    return task_id.split("-")[0] if "-" in task_id else "Core"


# Standard progress measures (Factories). Naming follows the existing records: "<Client> 1.1 Visitor to Lead".
# id, name, when, what it measures, HubSpot report, built by
FACTORIES = [
    ("0.1", "Database → Marketable database", "Every Marketing Hub customer", "% of contacts with lifecycle stage and original source set; marketable contacts; bounce rate under 2%.", "Contacts by lifecycle stage; email health", "4.05, MH-4.06, 4.07"),
    ("1.1", "Visitor → Lead", "Every Marketing Hub customer", "Visit-to-contact conversion rate; new contacts from forms per month.", "Sessions vs new contacts by source", "MH-5.01, MH-4.08"),
    ("1.2", "Lead → MQL", "Every Marketing Hub customer", "Lead-to-MQL rate; MQLs per month.", "Lifecycle stage funnel", "MH-5.02"),
    ("1.3", "MQL → Meeting", "Every Marketing Hub customer", "MQL-to-meeting rate; time to first sales touch.", "Funnel + meetings booked by source", "MH-5.03"),
    ("1.0", "Stranger → Visitor", "When ads, SEO or content is bought", "Sessions per month by source.", "Traffic analytics by source", "MH-5.05"),
    ("1.4", "Subscriber → Engaged", "When email programs are bought", "Email click rate; contacts engaged in the last 90 days.", "Email performance; engagement segment size", "MH-5.04"),
    ("2.1", "Lead → Contacted", "Every Sales Hub customer", "Share of leads contacted within 24 hours; time to first touch.", "Lead response time; contacts by lead status", "SH-5.01"),
    ("2.2", "Meeting → Qualified deal", "Every Sales Hub customer", "Meeting-to-deal rate.", "Meetings booked vs deals created", "SH-5.02"),
    ("3.1", "Deal → Proposal sent", "When pipeline automation is bought", "Stage conversion; days in stage.", "Deal stage funnel", "SH-5.03"),
    ("3.2", "Proposal → Closed won", "Every Sales Hub customer", "Win rate; sales cycle length.", "Deals won vs lost; cycle length", "SH-5.04"),
    ("4.1", "Ticket → Resolved", "Every Service Hub customer", "Time to first response; time to close; SLA hit rate.", "Help desk and SLA reports", "SV-5.01"),
    ("4.2", "Question → Self-served", "Every Service Hub customer", "Knowledge base views vs new tickets.", "Knowledge base and ticket volume", "SV-5.02"),
    ("4.3", "Customer → Renewed", "When customer success is bought", "Survey response, health score, renewal rate.", "Feedback surveys; customer success workspace", "SV-5.03"),
]

# Recommended request handling ($250 per request)
REQUEST_RULES = [
    "One request = one deliverable that takes up to about 2 hours (one email, one form, one workflow change, one report).",
    "Bigger than that becomes a scoped quote, not a request.",
    "Anything in the customer's plan (Task Template) is never a request.",
]
# class, what it is, response and turnaround, price
REQUEST_CLASSES = [
    ("Critical", "Something live is broken: forms not submitting, emails not sending, a workflow sending the wrong email, tracking down.", "Reply within 4 business hours; fixed within 1 business day.", "Free if it's in something we built; otherwise $250"),
    ("High", "Needed for a launch or deadline in the next 2 weeks.", "Reply within 1 business day; done within 5 business days.", "$250"),
    ("Standard", "A small new request with no hard deadline.", "Reply within 1 business day; done within 10 business days.", "$250"),
    ("Not now", "An idea or a bigger project for later.", "Logged and reviewed at MBRs and the 'what's next' call.", "Quoted when scoped"),
]

# Suggested scope limits for the new in-scope work
SCOPE_LIMITS = [
    ("Migration", "One previous email/marketing tool (e.g. Mailchimp): lists with consent and unsubscribes, up to 5 email templates, and the automations that are active today."),
    ("Website", "Connect the current website (tracking, forms, CTAs, chat, meetings), landing page and blog templates, up to 10 landing pages, blog import. A full website rebuild is a separate project."),
]

# offer, price, what's included
POST_PROGRAM = [
    ("KPI monitoring (6 months)", "Free", "Monthly KPI snapshot with Architect notes; portal health alerts; check-in calls at month 3 and month 6; requests still available at $250 each."),
    ("Team support", "$1,670/mo (existing 'Monthly Plan – Standard', 1 task at a time)", "Same Architect, ongoing requests one at a time, weekly office hours."),
    ("Build internal capacity", "To be priced", "Coach their in-house marketer or admin: monthly training plan, admin office hours, HubSpot certification path, help hiring a marketing ops role."),
    ("One initiative a month", "To be priced", "One scoped project per month from the 'not now' list (a new nurture, a campaign, a report pack, another tool migration)."),
]

# section, question, field type, required, already captured pre-sale?, why we ask, maps to
INTAKE = [
    ("Contacts", "Main point of contact (name, email, role)", "Text", "Yes", "Yes (confirm)", "One owner for approvals and to-dos.", "Deal contact: POC"),
    ("Contacts", "Supporters who should get updates or training", "Multi-line text", "Yes", "Partly", "Training plan and weekly update recipients.", "Deal contacts: Supporter"),
    ("Contacts", "Who controls your DNS / IT?", "Text", "Yes", "No", "Email authentication and domain connection.", "Customer project"),
    ("Contacts", "Preferred channel for quick questions", "Dropdown: Email / Slack Connect / Teams", "Yes", "No", "How office-hours follow-ups happen.", "Customer project"),
    ("Contacts", "Time zone and best days for office hours", "Text", "No", "No", "Office hours slots.", "Customer project"),
    ("Goals", "In one sentence: from where to where? (pre-filled from the sale)", "Multi-line text", "Yes", "Yes (confirm)", "The goal every update ties back to.", "Customer project"),
    ("Goals", "Top 3 results you want by the end of the program", "Multi-line text", "Yes", "Partly", "Prioritizes the build.", "Customer project"),
    ("Goals", "How do you report marketing results today, and to whom?", "Multi-line text", "Yes", "Partly", "Shapes dashboards and MBRs.", "Customer project"),
    ("Goals", "Current numbers: monthly sessions, leads, MQLs, meetings, customers", "Number fields", "No", "Partly", "Baselines for progress measures.", "Progress measures"),
    ("Audience", "Who are your buyers? (personas / segments)", "Multi-line text", "Yes", "No", "Segments and nurture.", "Customer project"),
    ("Audience", "How do you define a marketing-qualified lead today?", "Multi-line text", "Yes", "No", "Progress measures 1.2 and 1.3.", "Customer project"),
    ("Marketing today", "Channels you use", "Checkboxes: SEO, Paid search, Paid social, Organic social, Email, Events/Webinars, Partners, Outbound", "Yes", "Partly", "Integrations and optional progress measures.", "Customer project"),
    ("Marketing today", "Campaigns or launches planned in the next 90 days", "Multi-line text", "No", "No", "Pick the first campaign.", "Customer project"),
    ("Marketing today", "Who on your team will run HubSpot, and hours per week", "Text", "Yes", "Partly", "Training scope and a realistic timeline.", "Customer project"),
    ("Marketing today", "Other agencies or freelancers involved", "Text", "No", "No", "Avoid overlap.", "Customer project"),
    ("Approvals", "Who approves emails/pages before they go live, and how fast?", "Text", "Yes", "No", "Sign-off turnaround in the plan.", "Customer project"),
    ("Tech", "Marketing Hub tier", "Dropdown: Professional / Enterprise", "Yes", "Yes (confirm)", "Which setup items apply.", "Customer project"),
    ("Tech", "Website platform and who can edit it", "Dropdown + text", "Yes", "Partly", "Website connection.", "Customer project"),
    ("Tech", "Email domain you send from", "Text", "Yes", "No", "Email authentication.", "Customer project"),
    ("Migration", "Which email/marketing tool are you moving from, and what's active in it today?", "Text + multi-line text", "Yes", "Partly", "Migration plan.", "Customer project"),
    ("Migration", "Where do your contacts live today and roughly how many?", "Text + number", "Yes", "No", "Import scope and marketing contacts.", "Customer project"),
    ("Website", "Landing pages and blog posts to bring over (links or count)", "Multi-line text", "No", "No", "Website scope within the limit.", "Customer project"),
    ("Tech", "Other tools to connect (CRM, ads, webinar, chat, analytics)", "Multi-line text", "Yes", "Partly", "Integrations.", "Customer project"),
    ("Compliance", "Regions you market to and consent rules you follow", "Checkboxes: US, Canada (CASL), EU/UK (GDPR), Other", "Yes", "No", "Subscription types, consent, cookie banner.", "Customer project"),
    ("Compliance", "Industry regulations (e.g. HIPAA, financial)", "Text", "No", "No", "Data handling limits.", "Customer project"),
    ("Brand", "Upload brand guide, logos, fonts, email templates", "File upload", "Yes", "No", "Brand kit and templates.", "Supered upload"),
    ("Access", "Checklist: HubSpot access, website admin, GA4/GTM, ad accounts, social accounts, old tool login", "Checkboxes", "Yes", "Partly", "One list so access isn't chased for weeks.", "Supered to-do"),
    ("Sales Hub", "Which CRM or spreadsheet are you moving from, and how many open deals?", "Text + number", "If Sales Hub", "Partly", "CRM migration scope.", "Customers row"),
    ("Sales Hub", "Your sales stages today, and what has to be true to move a deal forward", "Multi-line text", "If Sales Hub", "No", "Pipeline design.", "Customers row"),
    ("Sales Hub", "How many reps, and how leads are assigned today", "Text", "If Sales Hub", "No", "Seats and lead rotation.", "Customers row"),
    ("Service Hub", "Which help desk are you moving from, and which channels do customers use (email, chat, phone)?", "Multi-line text", "If Service Hub", "Partly", "Channels and migration.", "Customers row"),
    ("Service Hub", "Response and resolution times you promise customers today", "Text", "If Service Hub", "No", "SLAs.", "Customers row"),
    ("Service Hub", "Do you run surveys (CSAT, NPS) or track renewals?", "Text", "If Service Hub", "No", "Progress measure 4.3.", "Customers row"),
]

# area, item, details, tier ("Pro & Ent" or "Ent only"), task id, owner
TECH_SETUP = [
    ("Account", "Users & permission sets", "Invite client users, set permissions by role, teams if needed.", "Pro & Ent", "4.01", "Architect"),
    ("Account", "Require 2FA", "For every user.", "Pro & Ent", "4.01", "Architect"),
    ("Account", "Single sign-on (SSO)", "If the client uses an identity provider.", "Ent only", "4.01", "Architect"),
    ("Account", "Brands / business units", "If they market more than one brand.", "Ent only", "4.01", "Architect"),
    ("Account", "Sandbox account", "Test workflows and changes before production.", "Ent only", "4.01", "Architect"),
    ("Tracking", "Tracking code on every domain", "CMS plugin or GTM. Verify with a test visit.", "Pro & Ent", "MH-4.02", "Architect"),
    ("Tracking", "Exclude internal traffic", "Client and RevGravy IPs/domains.", "Pro & Ent", "MH-4.02", "Architect"),
    ("Tracking", "Cookie consent banner", "Per the regions in the intake.", "Pro & Ent", "MH-4.02", "Architect"),
    ("Domains", "Connect content domain", "Landing pages / blog subdomain (e.g. go.client.com).", "Pro & Ent", "MH-4.03", "Architect"),
    ("Domains", "Email sending domain authentication", "SPF, DKIM, DMARC added by the client's DNS contact; verified in HubSpot.", "Pro & Ent", "MH-4.03", "Architect + client IT"),
    ("Email", "Subscription types", "Per content type; mapped to consent rules.", "Pro & Ent", "MH-4.04", "Architect"),
    ("Email", "Footer, address, default sender", "Compliant footer, real sender name.", "Pro & Ent", "MH-4.04", "Architect"),
    ("Email", "Brand kit & email templates", "Logo, colors, fonts; 2–3 reusable templates.", "Pro & Ent", "MH-4.04", "Architect"),
    ("Data", "Property audit", "Remove unused, add what the progress measures need. Naming convention documented.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Lifecycle stages & lead status", "Definitions agreed with the client; automation set.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Marketing contact rules", "Who is a marketing contact; keeps billing under control.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Custom behavioral events", "Track key product or site actions.", "Ent only", "4.05", "Architect"),
    ("Migration", "Old tool inventory", "Lists, segments, templates, active automations, integrations.", "Pro & Ent", "MH-4.06", "Architect"),
    ("Migration", "Export lists with consent", "Including unsubscribes and hard bounces to suppress.", "Pro & Ent", "MH-4.06", "Architect"),
    ("Data", "Import contacts & companies", "Mapped import, consent mapped, unsubscribes suppressed, dedupe, associations.", "Pro & Ent", "4.07", "Architect"),
    ("Data", "Data hygiene workflows", "Formatting, required fields, duplicates.", "Pro & Ent", "4.07", "Architect"),
    ("Website", "HubSpot forms on the site", "Replace or collect existing site forms.", "Pro & Ent", "MH-4.08", "Architect"),
    ("Website", "CTAs, chat & meetings on the site", "Placed on the pages that matter.", "Pro & Ent", "MH-4.08", "Architect"),
    ("Website", "Landing page & blog templates", "Matching the brand kit.", "Pro & Ent", "MH-4.08", "Architect"),
    ("Integrations", "GA4", "Connected for reporting.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Ad accounts", "Google, Meta, LinkedIn with conversion events.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Social accounts", "Connected for publishing and reporting.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Webinar, Slack, other apps", "As listed in the intake.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "CRM sync (if CRM isn't HubSpot)", "Field mapping, sync rules, lifecycle alignment.", "Pro & Ent", "4.09", "Architect"),
    ("Reporting", "Baseline dashboard", "One report per progress measure; baseline vs now.", "Pro & Ent", "4.10", "Architect"),
    ("QA", "End-to-end test", "Visit → form → contact → workflow → email → notification.", "Pro & Ent", "4.11", "Architect"),
    ("Lead capture", "Forms, CTAs, landing & thank-you pages", "Per offer.", "Pro & Ent", "MH-5.01", "Architect"),
    ("Segmentation", "Core segments", "Persona, lifecycle, engagement, customers, suppression.", "Pro & Ent", "MH-5.02", "Architect"),
    ("Automation", "Nurture workflows & emails", "Per persona / offer.", "Pro & Ent", "MH-5.02", "Architect"),
    ("Automation", "Lead scoring", "Fit + engagement score; MQL threshold.", "Pro & Ent", "MH-5.02", "Architect"),
    ("Automation", "MQL handoff", "Assignment, notifications, follow-up SLA.", "Pro & Ent", "MH-5.03", "Architect"),
    ("Email", "Re-engagement & sunset flows", "Keeps the list healthy.", "Pro & Ent", "MH-5.04", "Architect"),
    ("Campaigns", "Campaigns, UTMs & ad audiences", "Campaign object, UTM conventions, retargeting audiences.", "Pro & Ent", "MH-5.05", "Architect"),
    ("Migration", "Rebuild templates & automations", "Up to 5 templates; automations active today.", "Pro & Ent", "MH-5.06", "Architect"),
    ("Migration", "Parallel send, then switch off the old tool", "One parallel send to compare, then cancel the old tool.", "Pro & Ent", "MH-5.06", "Architect + Client POC"),
    ("Website", "Migrate landing pages & blog", "Up to 10 landing pages + blog import; redirects set.", "Pro & Ent", "MH-5.07", "Architect"),
    ("Reporting", "Marketing performance dashboard", "Traffic, leads, MQLs, emails, campaigns.", "Pro & Ent", "MH-5.09", "Architect"),
    ("Reporting", "Revenue attribution reports", "Multi-touch attribution.", "Ent only", "MH-5.09", "Architect"),
    ("AI", "Breeze / AI settings", "Brand voice and content tools within the agreed AI terms.", "Pro & Ent", "MH-5.10", "Architect"),
    # Sales Hub
    ("Sales setup", "Assign Sales Hub seats", "One per rep and manager.", "Pro & Ent", "SH-4.01", "Architect"),
    ("Sales setup", "Teams & permission sets", "Reps see their own deals; managers see the team.", "Pro & Ent", "SH-4.01", "Architect"),
    ("Sales setup", "Connect rep inboxes & calendars", "Email logging and meetings booking work for every rep.", "Pro & Ent", "SH-4.01", "Architect"),
    ("Pipelines", "One pipeline per sales motion", "New business, renewals, partners, as needed.", "Pro & Ent", "SH-4.02", "Architect"),
    ("Pipelines", "Stage exit criteria & probabilities", "Written down and agreed with the sales lead.", "Pro & Ent", "SH-4.02", "Architect"),
    ("Pipelines", "Required properties per stage", "Only what the stage really needs.", "Pro & Ent", "SH-4.02", "Architect"),
    ("Leads", "Lead status & lifecycle definitions", "Agreed with marketing.", "Pro & Ent", "SH-4.03", "Architect"),
    ("Leads", "Assignment rules", "Rotation or territory.", "Pro & Ent", "SH-4.03", "Architect"),
    ("Quotes", "Product library", "Products and prices the reps quote.", "Pro & Ent", "SH-4.04", "Architect"),
    ("Quotes", "Quote templates & e-signature", "Branded template; signature flow tested.", "Pro & Ent", "SH-4.04", "Architect"),
    ("CRM migration", "Field map approved by the client", "Old CRM fields → HubSpot properties.", "Pro & Ent", "SH-4.05", "Architect"),
    ("CRM migration", "Import companies, contacts & open deals", "With owners mapped.", "Pro & Ent", "SH-4.05", "Architect"),
    ("CRM migration", "Import activity history", "Where the old CRM allows it.", "Pro & Ent", "SH-4.05", "Architect"),
    ("Sales integrations", "Calling and video meetings", "HubSpot calling or their provider; Zoom or Teams.", "Pro & Ent", "SH-4.06", "Architect"),
    ("Sales integrations", "LinkedIn Sales Navigator", "If they use it.", "Pro & Ent", "SH-4.06", "Architect"),
    ("Sales automation", "Lead rotation & task queues", "New leads land with the right rep and in a queue.", "Pro & Ent", "SH-5.01", "Architect"),
    ("Sales automation", "First-touch sequence", "Approved by the sales lead.", "Pro & Ent", "SH-5.01", "Architect"),
    ("Sales automation", "Qualification properties & playbooks", "Same questions on every discovery call.", "Pro & Ent", "SH-5.02", "Architect"),
    ("Sales automation", "Closed-won handoff workflow", "Notifies onboarding or service with the deal context.", "Pro & Ent", "SH-5.04", "Architect"),
    ("Sales automation", "Closed-lost reasons", "Required when a deal is lost.", "Pro & Ent", "SH-5.04", "Architect"),
    ("Sales reporting", "Pipeline dashboard & forecast", "Pipeline by stage, forecast, goals.", "Pro & Ent", "SH-5.06", "Architect"),
    # Service Hub
    ("Service setup", "Assign Service Hub seats", "One per support agent and lead.", "Pro & Ent", "SV-4.01", "Architect"),
    ("Service setup", "Help desk workspace & business hours", "Agents work tickets from one place.", "Pro & Ent", "SV-4.01", "Architect"),
    ("Channels", "Support email connected", "Replies go out from the help desk.", "Pro & Ent", "SV-4.02", "Architect"),
    ("Channels", "Chat & support form", "On the website and help pages.", "Pro & Ent", "SV-4.02", "Architect"),
    ("Tickets", "Ticket pipelines & stages", "Matches how the team works today.", "Pro & Ent", "SV-4.03", "Architect"),
    ("Tickets", "Priority, category & routing rules", "Tickets reach the right agent.", "Pro & Ent", "SV-4.03", "Architect"),
    ("Help desk migration", "Import open tickets & history", "From the old help desk.", "Pro & Ent", "SV-4.04", "Architect"),
    ("Help desk migration", "Import knowledge base articles", "Then fix formatting and links.", "Pro & Ent", "SV-4.04", "Architect"),
    ("SLAs", "SLA rules by priority", "First response and time to close.", "Pro & Ent", "SV-4.05", "Architect"),
    ("Service automation", "Ticket automation & snippets", "Auto-replies, assignment, saved replies.", "Pro & Ent", "SV-5.01", "Architect"),
    ("Knowledge base", "Structure & top 20 articles", "Covers the most common questions.", "Pro & Ent", "SV-5.02", "Architect"),
    ("Feedback", "CSAT or NPS surveys", "Sent after tickets close or on a schedule.", "Pro & Ent", "SV-5.03", "Architect"),
    ("Feedback", "Customer success workspace & health scores", "If customer success is bought.", "Ent only", "SV-5.03", "Architect"),
    ("Service reporting", "Help desk & SLA dashboard", "Volume, response times, SLA hits, CSAT.", "Pro & Ent", "SV-5.04", "Architect"),
]

# module, audience, content, format, when, length
TRAINING = [
    ("T1 · HubSpot basics", "All client users", "Navigation, records, notifications, where to find help.", "Supered tour + video", "After access (≈ Day 7)", "10 min"),
    ("T2 · Contacts & segments", "Marketing team", "Contact records, properties, segments, data hygiene habits.", "Video + office hours practice", "After data import (≈ Day 25)", "20 min"),
    ("T3 · Email marketing", "Marketing team", "Build, test, send and analyze emails with your templates.", "Video + live build in office hours", "After email foundations (≈ Day 20)", "25 min"),
    ("T4 · Forms, landing pages & CTAs", "Marketing team", "Create and edit lead capture assets.", "Video", "After 1.1 ships (≈ Day 40)", "20 min"),
    ("T5 · Workflows & nurture", "HubSpot admin(s)", "Read, edit and safely clone workflows.", "Live session", "After 1.2 ships (≈ Day 55)", "30 min"),
    ("T6 · Campaigns, ads & social", "Marketing team", "Campaigns, UTMs, ads and social reporting.", "Video", "After first campaign (≈ Day 65)", "20 min"),
    ("T7 · Reporting & dashboards", "Marketing lead + leadership", "Read the progress-measure dashboard; build a report.", "Live at MBR #2", "≈ Day 60", "20 min"),
    ("T8 · Lead handoff", "Marketing + sales", "MQL definition, notifications, follow-up SLA.", "Live session", "After 1.3 ships (≈ Day 60)", "20 min"),
    ("T9 · Admin handbook", "HubSpot admin(s)", "How your portal is built and how to maintain it.", "Supered Base", "≈ Day 85", "Self-serve"),
    ("S1 · CRM every day", "Sales reps", "Records, tasks, inbox, logging calls and emails.", "Video + office hours practice", "After inboxes connect (≈ Day 14)", "20 min"),
    ("S2 · Pipeline & deals", "Sales reps + manager", "Moving deals, stage rules, required fields.", "Live session", "After pipelines (≈ Day 20)", "25 min"),
    ("S3 · Sequences & templates", "Sales reps", "Enroll, personalize and track sequences.", "Video", "After 2.1 ships (≈ Day 40)", "20 min"),
    ("S4 · Quotes & closing", "Sales reps", "Build a quote, send it for signature, close the deal.", "Video", "After 3.2 ships (≈ Day 60)", "20 min"),
    ("S5 · Forecast & reports", "Sales manager", "Forecast, goals, pipeline and activity reports.", "Live at MBR #2", "≈ Day 60", "20 min"),
    ("V1 · Help desk basics", "Support team", "Working tickets, snippets, internal notes.", "Video + office hours practice", "After channels connect (≈ Day 18)", "20 min"),
    ("V2 · SLAs & routing", "Support lead", "How routing and SLAs work, and how to change them.", "Live session", "After SLAs (≈ Day 25)", "20 min"),
    ("V3 · Knowledge base", "Support team", "Write, publish and update articles.", "Video", "After 4.2 ships (≈ Day 60)", "20 min"),
    ("V4 · Feedback & customer success", "Support lead + CS", "Read surveys and health scores, and follow up.", "Video", "After 4.3 ships (≈ Day 65)", "20 min"),
    ("V5 · Service reports", "Support lead", "Help desk, SLA and CSAT reports.", "Live at MBR #2", "≈ Day 60", "20 min"),
]

# touchpoint, timing, channel, owner, content
COMMS = [
    ("Welcome email #1", "Day 0", "Email from Phil", "Ops (automated)", "Welcome, Supered Action Plan link, kickoff booking link, first to-dos (access + intake)."),
    ("Welcome email #2", "Day 2", "Email", "Ops (automated)", "How we work: office hours, weekly updates, requests and urgency classes ($250), escalation path, AI use."),
    ("Access / intake reminders", "Day 3–5 if incomplete", "Email", "Architect", "Friendly reminder listing the exact missing items."),
    ("Supered announcement", "Day 2–3", "Supered", "Architect", "How Supered works: Bases, announcements, documentation."),
    ("Kickoff (15 min)", "Day 5–10", "Video call", "Architect", "Intros, plan, missing items, office hours, MBRs."),
    ("Kickoff recap", "Within 24h of kickoff", "Email", "Architect", "Decisions, owners, dates, client to-dos."),
    ("Weekly update", "Every Friday", "Email", "Architect (AI draft)", "1) Work done and the strategic issue it moves  2) Numbers vs baseline  3) Issues found outside scope  4) Next week  5) Your to-dos."),
    ("Delivery announcement", "Each delivery", "Supered video", "Architect", "What was built, how to use it, why it matters."),
    ("Office hours", "Weekly slots", "Booking link", "Architect", "Questions, coaching, training practice."),
    ("MBR", "Monthly (≈ Day 30 and 60)", "Video call", "Architect (Phil optional)", "Progress vs baseline, numbers trend, issues and opportunities."),
    ("What's next", "≈ 30 days before the end", "Video call", "Architect", "Long-term vision, A/B next phase."),
    ("Final results review", "Last week of the program", "Video call", "Architect", "Before vs after, what we built, what's open."),
    ("KPI snapshot", "Monthly for 6 months after", "Scheduled dashboard email", "Architect", "Progress measures + 3 short notes."),
]

# criterion, HubSpot Work, Projects object, Tickets — each cell: (score 0-2, note). Kept as the record of the comparison.
TOOL_FIT = [
    ("One record per customer program", (2, "One project per customer, from a template"), (2, "Native CRM record"), (1, "Built for single requests")),
    ("Reusable task template", (2, "Duplicate the template project"), (1, "Templates still maturing"), (1, "Workflow-created tasks only")),
    ("Board, timeline, due dates", (2, "Board, timeline and calendar views"), (2, "Gantt, board, table, calendar"), (0, "Board only")),
    ("Sections per phase", (2, "Tasks grouped by section"), (1, "Pipeline stages"), (1, "Pipeline stages")),
    ("Client can see their plan", (0, "Internal only (Supered covers this)"), (2, "Customer portal"), (1, "Customer portal")),
    ("Request log with urgency", (2, "Request table in each project"), (0, "Not its job"), (2, "Ticket pipeline")),
    ("Maturity", (0, "Public beta"), (2, "Generally available"), (2, "Generally available")),
]

WHERE_IT_LIVES = [
    ("HubSpot Work", "The whole onboarding: one shared set of tables for all customers (Customers, Customer Task, Request, Update), a template task list, board, timeline and agents."),
    ("Supered", "Everything the customer sees: Action Plan, announcements, delivery and training videos, admin handbook."),
    ("HubSpot CRM", "The deal-stage gate, the two welcome emails, meetings links and the dashboards that report progress measures."),
    ("Not used for onboarding", "Projects object pipelines, tickets, HubSpot customer portal, Trello."),
]

# HubSpot Work structure — used by the sheet and the prompts.
# Checked against the build (Oct 2026): HubSpot Work has no custom project fields, and project copies don't carry
# agent workflows. So every customer shares the same tables, and each row links to its Customers row. The template
# 'Onboarding Task Library' project's Task Library table is the master list (Core + one module per hub) the Task Generator copies from.
WORK_TIMEZONE = "America/Bogota"   # the team works on Bogotá time
WORK_STATUSES = ["Not started", "In progress", "Waiting on client", "In review", "Done", "Won't do"]
WORK_TASK_COLUMNS = [
    ("Task ID", "Text", "e.g. 4.07 (Core) or MH-4.03 (Marketing Hub). First column, so 'Depends on' can be read"),
    ("Task", "Text", "Task name"),
    ("Module", "Dropdown", "Core, Marketing Hub, Sales Hub, Service Hub"),
    ("Status", "Dropdown", ", ".join(WORK_STATUSES)),
    ("Owner role", "Dropdown", ", ".join(ROLES)),
    ("Assignee", "HubSpot user", "Person doing it"),
    ("Due date", "Formula", "Project Day 0 + Due day, compressed by Program length (see rule)"),
    ("Client-facing", "Yes/No", "Does the customer see or do this?"),
    ("Repeats", "Text", "Weekly, Monthly, etc."),
    ("Depends on", "Text", "Task IDs"),
    ("Definition of done", "Long text", "What 'done' means"),
    ("Notes", "Long text", "Anything else"),
    ("Section", "Dropdown", "Phase: P0 to P9 (hidden in Main table)"),
    ("Start day", "Number", "Days after Day 0, 90-day plan (hidden)"),
    ("Due day", "Number", "Days after Day 0, 90-day plan (hidden)"),
    ("Start date", "Date", "Optional, for the Timeline view (hidden)"),
    ("Project Day 0", "Date", "Helper for the formula: the customer's Start date, filled by the Task Generator (hidden)"),
    ("Program length", "Number", "Helper for the formula: 60, 75 or 90, filled by the Task Generator (hidden)"),
]
WORK_VIEWS = [
    ("Board", "Columns = Status. Cards show Customer, Task ID, Task, Assignee, Due date."),
    ("By customer", "List grouped by Customer, then Section, sorted by Task ID."),
    ("By section", "List grouped by Section (P0 → P9), sorted by Task ID."),
    ("By module", "Grouped by Module, then Section."),
    ("Timeline", "Start date → Due date, grouped by Customer."),
    ("Calendar", "By Due date."),
    ("My tasks", "Assignee = me, Status not Done / Won't do."),
    ("Client to-dos", "Owner role = Client POC, Status not Done."),
    ("This week", "Due date in the next 7 days, Status not Done."),
    ("Overdue", "Due date before today, Status not Done / Won't do."),
]
WORK_REQUEST_COLUMNS = [
    ("Customer", "Link to Customers row"), ("Owner", "HubSpot user, defaults to the customer's Architect"),
    ("Request", "Text"), ("Urgency", "Dropdown: Critical, High, Standard, Not now"),
    ("Type", "Dropdown: Client request, Issue found, Client idea"), ("Status", "Dropdown: New, Quoted, In progress, Done, Parked"),
    ("Price", "Number in USD, default 250"), ("Logged on", "Date"), ("Due date", "Date"), ("Notes", "Long text"),
]
WORK_UPDATE_COLUMNS = [
    ("Customer", "Link to Customers row"),
    ("Type", "Dropdown: Handoff brief, Weekly update, What's next options, KPI snapshot, Delay flag"),
    ("Period", "Date: week of, or month"), ("Draft", "Long text"),
    ("Status", "Dropdown: Draft (an agent wrote it), Reviewed (the Architect checked it), Sent (the Architect sent it to the customer)"), ("Notes", "Long text"),
]
WORK_UPDATE_VIEWS = [
    ("To review", "Status = Draft, grouped by Customer."),
    ("By customer", "Grouped by Customer, newest first."),
]
WORK_PORTFOLIO_COLUMNS = [
    ("Customer", "Text: client name"),
    ("Company", "CRM company"), ("Deal", "CRM deal"), ("Architect", "HubSpot user"),
    ("Program length", "Number: 60, 75 or 90"), ("Start date", "Date: Day 0 = the day the deal reached Start Payment Received, not the kickoff date"), ("Target end date", "Date"),
    ("Hub tiers", "Text, e.g. Marketing Pro, Sales Enterprise"), ("Health", "Dropdown: On track, At risk, Off track"),
    ("Current section", "Dropdown: P0–P9, Completed"), ("Next MBR", "Date, filled by the Architect when booked"),
    ("Next due task", "Text"),
    ("Products purchased", "Multi-select: Marketing Hub Onboarding, Sales Hub Onboarding, Service Hub Onboarding"),
    ("Create tasks", "Checkbox: Ops ticks it to create or add tasks"),
    ("Tasks created for", "Multi-select, same options: set by the Task Generator"),
    ("From→To goal", "Long text"), ("Progress measures", "Long text: name, baseline, target"),
    ("FigJam link", "URL"), ("Supered Action Plan link", "URL"),
]
WORK_PORTFOLIO_VIEWS = [
    ("Capacity", "Report: active customers per Architect. Phil uses it to pick the Architect."),
    ("Health board", "Columns = Health."),
    ("Ending soon", "Target end date in the next 35 days (time for the 'what's next' call)."),
]

# How a new customer gets set up.
NEW_CUSTOMER_STEPS = [
    "Add a row to Customers: Customer, Company, Deal, Architect, Program length, Start date (the payment date), Products purchased, hub tiers, From→To goal, FigJam and Supered links.",
    "Tick Create tasks. The Task Generator copies the Core tasks once, plus one module for each product purchased, into Customer Task. It fills the dates, assigns the Architect, sets Tasks created for, and unticks Create tasks.",
    "If the customer buys another hub later, add it to Products purchased and tick Create tasks again. Only the new hub's tasks are added.",
    "To work on one customer, filter any view by Customer. 'My tasks' shows an Architect's work across all their customers.",
    "Share the workspace with Phil and the Architects (it's private by default).",
]

# HubSpot Work agents, one prompt each for the agent builder. All live in the Onboarding Portfolio project.
# Every agent only drafts, fills fields or flags; none sends anything to a customer or changes a deal.
WORK_AGENTS = [
    {"name": "Onboarding Task Generator", "sample": "Auto-create customer onboarding",
     "trigger": "Create tasks is ticked on a Customers row.",
     "summary": "Copies the Core tasks plus one module per product purchased into Customer Task, fills the dates and assigns the Architect.",
     "steps": [
         "Check the row has Start date, Program length, Architect and at least one Products purchased value. If any is missing, untick Create tasks and tell the person who ticked it what's missing.",
         "Work out which modules to copy. Core: only if Tasks created for is empty. Then each product in Products purchased that isn't in Tasks created for yet: Marketing Hub Onboarding = Module 'Marketing Hub', Sales Hub Onboarding = 'Sales Hub', Service Hub Onboarding = 'Service Hub'.",
         "For each of those modules, copy every row of the Task Library table (in the 'Onboarding Task Library' project) whose Module matches into Customer Task. Keep Task ID, Task, Module, Section, Owner role, Client-facing, Start day, Due day, Repeats, Depends on, Definition of done and the subtasks. Set Customer = this row and Status = Not started.",
         "On the new rows, set Program length = the row's Program length and Project Day 0 = the row's Start date. For a module added after the first run (an upsell), set Project Day 0 = today instead.",
         "Set Assignee = the row's Architect on every new task whose Owner role is Architect.",
         "On the Customers row: add the products just created to Tasks created for, set Target end date = Start date + Program length days if it's empty, set Current section = P1 and Health = On track on the first run, then untick Create tasks.",
         "Notify the Architect: which modules were added and how many tasks, with a link to Customer Task filtered to this customer.",
     ],
     "rules": [
         "Never copy a module that is already in Tasks created for, and never copy Core twice.",
         "Never change or delete existing Customer Task rows.",
         "If the subtasks can't be copied, copy the tasks and say so in the notification.",
     ]},
    {"name": "Handoff Brief", "sample": None,
     "trigger": "Tasks created for changes from empty to having a value on a Customers row (the first time a customer's tasks are created).",
     "summary": "Writes a one-page brief for the Architect from the deal's history.",
     "steps": [
         "Read the CRM deal on the Customers row: its notes, meetings, emails, quote and line items. Also read the row's From→To goal, Progress measures and FigJam link.",
         "Write a one-page brief: who the customer is, the From→To goal, what they bought, the progress measures, the people involved (POC, supporters, decision maker), risks, and open questions for the handoff call.",
         "List any pre-sale item that looks missing: FigJam link, From→To statement, products, progress measures, survey, POC and supporters, signed agreement.",
         "Add it to the Update table: Customer = this customer, Type = Handoff brief, Status = Draft.",
         "Notify the Architect and Phil.",
     ],
     "rules": ["Internal only. Never contact the customer.", "If there's no deal on the row, write what you can and say the deal is missing."]},
    {"name": "Weekly Update Drafter", "sample": "Weekly stakeholder updates",
     "trigger": f"Every Thursday at 9:00 AM ({WORK_TIMEZONE}).",
     "summary": "Drafts each customer's Friday update for the Architect to review and send.",
     "steps": [
         "For each Customers row whose Current section is P2 to P8, look at that customer's Customer Task and Requests.",
         "Draft the update in five parts: 1) what we did this week and which strategic issue it moves (tie it to the From→To goal), 2) numbers vs baseline, 3) issues found that are outside scope, 4) what we'll do next week, 5) the client's to-dos.",
         "Use: tasks that became Done in the last 7 days; tasks due in the next 7 days; tasks with Owner role Client POC that aren't Done; Requests logged in the last 7 days with Type Issue found or Client idea.",
         "For part 2, write '[Architect: add this week's numbers from the dashboard]' unless numbers are in the row's Progress measures.",
         "Add it to the Update table: Customer, Type = Weekly update, Period = this Friday's date, Status = Draft. Notify the Architect.",
     ],
     "rules": ["Short and plain: no more than about 200 words.", "One draft per customer per week. If one already exists and is still Draft, update it instead. Never change one that is Reviewed or Sent.", "Never send it to the customer. The Architect reviews it (Status = Reviewed), sends it, then sets Status = Sent."]},
    {"name": "Delay Flagger", "sample": None,
     "trigger": f"Every weekday at 8:00 AM ({WORK_TIMEZONE}).",
     "summary": "Flags overdue and stuck tasks and sets Health to At risk.",
     "steps": [
         "For each Customers row that isn't Completed, find that customer's Customer Task that are past their Due date with Status not Done or Won't do, and tasks that have been 'Waiting on client' for more than 3 days.",
         "Send the Architect one message per customer listing those tasks, with links.",
         "If a customer has 3 or more overdue tasks and Health is On track, set Health = At risk.",
         "When Health changes to At risk or Off track, also notify Phil.",
     ],
     "rules": ["Don't change task dates, statuses or assignees.", "Send nothing when there's nothing to flag.", "Never set Health back to On track; the Architect does that."]},
    {"name": "Request Triage", "sample": "Auto-route requests",
     "trigger": "A new row is added to the Request table.",
     "summary": "Suggests the urgency class, price and due date for each new request.",
     "steps": [
         "Read the Request and Notes and set Urgency: Critical = something live is broken (forms not submitting, emails not sending, a workflow sending the wrong email, tracking down). High = needed for a launch or deadline in the next 2 weeks. Standard = small, no hard deadline. Not now = an idea or a bigger project for later.",
         "If Owner is empty, set it to the customer's Architect.",
         "Set Due date from Logged on: Critical = 1 business day, High = 5 business days, Standard = 10 business days, Not now = leave empty.",
         "Set Price: 250 for High and Standard. For Critical, 0 if it's in something we built, otherwise 250. Not now = empty.",
         "If it looks bigger than about 2 hours of work (one email, one form, one workflow change, one report), set Status = Quoted and explain why in Notes.",
         "Notify the Owner, and remind them of the reply time: within 4 business hours for Critical, within 1 business day for High and Standard. For Critical, also notify Phil right away.",
     ],
     "rules": ["The Architect can override anything you set.", "Never reply to the customer.", "If Customer is empty, ask the person who added the row to fill it.", "Price is in USD. The default 250 is not the customer's approval; paid work waits for their OK."]},
    {"name": "Portfolio Sync", "sample": None,
     "trigger": f"Every day at 6:00 AM ({WORK_TIMEZONE}).",
     "summary": "Keeps each customer's Current section and Next due task up to date.",
     "steps": [
         "For each Customers row that isn't Completed, look at that customer's Customer Task.",
         "Set Current section = the earliest section that still has open tasks (Status not Done or Won't do). Ignore P0 and P7, which run the whole program. Ignore P9 until the Target end date has passed.",
         "Set Next due task = the open task with the earliest Due date, written as 'Task ID Task (date)'.",
         "If every task in P1 to P8 is Done or Won't do and the Target end date has passed, set Current section = P9.",
     ],
     "rules": ["Only change Current section and Next due task.", "Don't touch Next MBR; the Architect fills it."]},
    {"name": "What's Next Prep", "sample": None,
     "trigger": f"Every day at 7:00 AM ({WORK_TIMEZONE}), for Customers rows whose Target end date is 35 days away or less and that don't have a 'What's next options' update yet.",
     "summary": "Prepares Option A and Option B for the 'what's next' call.",
     "steps": [
         "Read the customer's Weekly update drafts, their Progress measures, and their Requests with Type Issue found or Client idea, or Urgency Not now.",
         "Write: results so far vs baseline; issues found; ideas parked as 'not now'; then Option A and Option B for the next phase. Add which after-program offer fits: team support ($1,670/mo Monthly Plan), building internal capacity, or one initiative a month. Every customer also gets 6 months of free KPI monitoring.",
         "Add it to the Update table: Type = What's next options, Status = Draft.",
         "Notify the Architect, and ask Phil to review it before the call.",
     ],
     "rules": ["One per customer.", "Internal only. Never contact the customer."]},
    {"name": "KPI Snapshot Drafter", "sample": None,
     "trigger": f"The 1st of every month at 9:00 AM ({WORK_TIMEZONE}).",
     "summary": "Drafts the monthly KPI notes during the 6 months of free monitoring.",
     "steps": [
         "Find Customers rows whose Target end date is in the past, but less than 6 months ago.",
         "For each one, draft 3 short notes on their progress measures: what moved, what didn't, one suggestion. Use '[Architect: add numbers]' where you don't have them.",
         "Add it to the Update table: Type = KPI snapshot, Period = this month, Status = Draft. Notify the Architect, who sends it with the dashboard email.",
     ],
     "rules": ["Stop for a customer once 6 months have passed since their Target end date.", "Never send it to the customer."]},
]

OPEN_QUESTIONS = []


# ---------------------------------------------------------------------------
# The journey: a worked example of one customer from sale to month 6 after.
# Lanes: customer, phil, architect, ops, work (what changes in HubSpot Work).
# "done" lists the Task IDs marked Done (or Won't do) at that moment.
# ---------------------------------------------------------------------------

EXAMPLE = {
    "customer": "Northpeak Outfitters",
    "note": "A made-up customer used to show the flow.",
    "day0": "2026-11-02",          # Monday the deal reaches Start Payment Received
    "tier": "Marketing Hub Professional",
    "program_days": 90,
    "measures": "0.1, 1.1, 1.2, 1.3 (didn't buy 1.0 or 1.4)",
    "migration": "Moving from Mailchimp; website on WordPress",
}

LANES = [
    ("customer", "Customer", "The POC and their team. They see emails, Supered and calls. They never see HubSpot Work."),
    ("phil", "Phil", "Leads the sale and the handoff, picks the Architect, reviews next-phase options."),
    ("architect", "Architect", "Owns the customer after the handoff and keeps every status in HubSpot Work current."),
    ("ops", "Ops", "Adds the customer to HubSpot Work and sets up Supered."),
    ("work", "HubSpot Work", "What changes in the tables, and which agent runs."),
]

JOURNEY = [
    {"stage": "Before the sale", "start": -30, "end": -1, "title": "The deal is being won",
     "customer": ["Watches the VSL, has the Fit call, fills the tech stack survey and watches the recommendation video.",
                  "Joins the proposal Q&A, signs the agreement (AI terms, escalation path, $250 requests) and pays."],
     "phil": ["Writes the research brief, builds the FigJam after the Fit call and captures the From→To statement.",
              "Builds the quote, picks the progress measures and adds the POC and supporters to the deal.",
              "Checks the Capacity report when the proposal goes out, so an Architect is ready."],
     "architect": [], "ops": [],
     "work": ["Nothing yet. A customer only gets a row once they pay, so deals that don't close never clutter Work."],
     "done": []},
    {"stage": "Week 1", "start": 0, "end": 0, "title": "Payment lands",
     "customer": ["Gets welcome email #1 from Phil within minutes: the Supered Action Plan, the kickoff booking link and two to-dos (grant HubSpot access, fill the intake form)."],
     "phil": ["Opens the Capacity report, picks the Architect and tells Ops."],
     "architect": ["Gets two notifications: the tasks are ready, and the Handoff Brief draft is waiting."],
     "ops": ["Adds the Customers row within 4 business hours: Customer, Company, Deal, Architect, Program length, Start date (the payment date), Products purchased = Marketing Hub Onboarding, tier, From→To goal, FigJam and Supered links. Then ticks Create tasks.",
             "Builds the Supered Action Plan from the template and checks welcome email #1 went out."],
     "work": ["The Task Generator copies the Core tasks and the Marketing Hub module (74 rows) into Customer Task with due dates, assigns the Architect's tasks, sets Target end date, Tasks created for = Marketing Hub Onboarding, Current section = P1 and Health = On track, and unticks Create tasks.",
              "Handoff Brief writes a one-page draft in the Update table for the Architect and Phil."],
     "done": ["1.01", "1.02", "1.03", "1.04"]},
    {"stage": "Week 1", "start": 1, "end": 3, "title": "Handoff",
     "customer": ["Gets welcome email #2 on Day 2: how office hours, Friday updates, requests and escalation work.",
                  "Books the 15-minute kickoff."],
     "phil": ["Runs the 30-minute handoff call with the Architect, using the Handoff Brief.",
              "Fixes any missing pre-sale item within 24 hours. From here on the Architect is the strategy lead."],
     "architect": ["Walks the P0 checklist: marks each item Done only if it's really there; anything missing goes back to Phil.",
                   "Writes the progress measures with baselines and targets into the Customers row.",
                   "Sets Won't do on what this customer didn't buy (MH-5.04 and MH-5.05 here, plus Enterprise-only subtasks for a Pro customer), with a note.",
                   "Adds the office hours link to Supered and marks the Handoff Brief Reviewed."],
     "ops": [],
     "work": ["Handoff Brief moves to Reviewed in the Update table.",
              "Portfolio Sync runs every day at 6:00 AM from now on, keeping Current section and Next due task current."],
     "done": ["0.01", "0.02", "0.03", "0.04", "0.05", "0.06", "0.07", "0.08", "1.05", "1.06", "1.07", "1.08", "1.09"],
     "wont": ["MH-5.04", "MH-5.05"]},
    {"stage": "Week 1", "start": 1, "end": 7, "title": "Access and intake",
     "customer": ["Works through the Supered to-do list: grants HubSpot access, fills the intake form, shares DNS, WordPress, GA4, ad and social access and the Mailchimp login, uploads brand files.",
                  "Gets a short Supered video on how updates and documentation will reach them."],
     "phil": [],
     "architect": ["Sets the customer's tasks to Waiting on client, and marks them Done only once the access works or the form is in.",
                   "Chases on Day 3 if access isn't granted.",
                   "Runs the portal audit and records the baseline numbers."],
     "ops": [],
     "work": ["Delay Flagger (weekdays, 8:00 AM) flags anything past due or Waiting on client for more than 3 days.",
              "The Customers row now holds the baselines."],
     "done": ["2.01", "2.02", "2.03", "2.04", "2.05", "2.06", "2.07"]},
    {"stage": "Week 1–2", "start": 5, "end": 10, "title": "Kickoff",
     "customer": ["Has a 15-minute call: meets the Architect and team, confirms the goal and plan, hears how office hours, Friday updates, MBRs and requests work.",
                  "Gets calendar invites for MBR #1, MBR #2, the what's next call and the final review, and a recap within 24 hours."],
     "phil": ["Optional: joins for the first few minutes."],
     "architect": ["Drafts the agenda from the intake and the audit, then runs the call.",
                   "Books the MBRs and fills Next MBR on the Customers row.",
                   "Confirms who needs which training modules.",
                   "Sends the recap and updates the Supered plan."],
     "ops": [],
     "work": ["Next MBR is filled. Current section moves to P4 as the P1–P3 tasks close."],
     "done": ["3.01", "3.02", "3.03", "3.04", "6.01"]},
    {"stage": "Weeks 2–4", "start": 7, "end": 30, "title": "Foundations",
     "customer": ["Their IT contact adds the DNS records for email authentication.",
                  "Gets a Supered video when the foundations are done."],
     "phil": [],
     "architect": ["Works through 4.01–4.11, ticking subtasks. A task is Done when every subtask is ticked or marked not applicable.",
                   "Moves tasks blocked on the customer's IT (like MH-4.03) to Waiting on client.",
                   "Foundation QA (4.11): when the end-to-end test passes, foundations are done. Records the Supered video (4.12)."],
     "ops": [],
     "work": ["Tasks move across the Board from Not started to In progress to Done. The Overdue view and Delay Flagger catch anything slipping."],
     "done": ["4.01", "MH-4.02", "MH-4.03", "MH-4.04", "4.05", "MH-4.06", "4.07", "MH-4.08", "4.09", "4.10", "4.11", "4.12"]},
    {"stage": "Every week", "start": 7, "end": 90, "title": "The weekly rhythm",
     "customer": ["Books office hours when they need help, and sends requests whenever they come up.",
                  "Gets the Friday update: work done and why it matters, numbers vs baseline, issues found, next week, their to-dos."],
     "phil": ["Runs a weekly delivery review with the Architects using the Health board, the Overdue view and the Capacity report."],
     "architect": ["Monday: plans the week from My tasks and This week.",
                   "Logs every request the day it arrives.",
                   "Friday: opens the Weekly update draft, adds the week's numbers from the dashboard, sends it, marks it Sent and sets Health."],
     "ops": [],
     "work": ["Thursday 9:00 AM: Weekly Update Drafter writes the draft.",
              "Weekdays 8:00 AM: Delay Flagger. Daily 6:00 AM: Portfolio Sync.",
              "Recurring P7 tasks stay In progress until close-out; each Sent update is the record that the week happened."],
     "done": []},
    {"stage": "Weeks 3–11", "start": 21, "end": 75, "title": "Build and launch",
     "customer": ["Reviews and approves each build: copy, forms, nurture emails, and the MQL handoff with their sales team.",
                  "Confirms Mailchimp can be switched off after one parallel send.",
                  "Gets a Supered video per delivery, and the training module for each feature as it ships."],
     "phil": [],
     "architect": ["Builds one progress measure at a time: 1.1 Visitor → Lead, then 1.2 Lead → MQL, then 1.3 MQL → Meeting.",
                   "Sets a build to In review while it waits for sign-off, and marks it Done only after sign-off and go-live.",
                   "Moves the landing pages and blog within the limits, and launches the first campaign with the customer."],
     "ops": [],
     "work": ["In review shows what's waiting on the customer. The Client to-dos view lists everything they owe."],
     "done": ["MH-5.01", "MH-5.02", "MH-5.03", "MH-5.06", "MH-5.07", "MH-5.08", "MH-5.09", "MH-5.10", "5.11", "5.12", "MH-6.02"],
     "note": "In the example, Thanksgiving (Day 24) and Christmas (Day 53) fall in this stretch. Plan customer sign-offs around them."},
    {"stage": "Months 1–2", "start": 30, "end": 60, "title": "Monthly Business Reviews",
     "customer": ["MBR #1 (about Day 30) and MBR #2 (about Day 60): progress vs baseline on each progress measure, what we found, what's next."],
     "phil": ["Optional at MBR #1. Joins MBR #2 if there's a commercial topic."],
     "architect": ["Runs each MBR from the dashboard and the Friday updates, and updates Next MBR.",
                   "Day 45: adoption check (logins, emails sent, workflows on)."],
     "ops": [],
     "work": ["Next MBR moves to the next date."],
     "done": ["6.03"]},
    {"stage": "Day 55", "start": 55, "end": 55, "title": "What's next prep",
     "customer": [],
     "phil": ["Reviews Option A and Option B before the call."],
     "architect": ["Edits the draft: results, issues found, 'not now' ideas, two next-phase options and the offer that fits."],
     "ops": [],
     "work": ["What's Next Prep fires 35 days before the Target end date and writes the draft in the Update table.",
              "The customer shows up in the Ending soon view."],
     "done": ["8.01"],
     "note": "In the example, Day 55 is Sunday, Dec 27. The agent still runs; the Architect edits the draft on Monday."},
    {"stage": "Day 60–65", "start": 60, "end": 65, "title": "The what's next call",
     "customer": ["Sees the results so far and the long-term vision, chooses Option A or B, and hears about the 6 months of free KPI monitoring."],
     "phil": ["Helps price the proposal if needed."],
     "architect": ["Runs the call.",
                   "Creates the next-phase deal in the Sales Pipeline and sends the proposal."],
     "ops": [],
     "work": ["The What's next options update is marked Sent."],
     "done": ["8.02", "8.03"],
     "note": "In the example, Day 60 is New Year's Day. Book the call for Jan 4–6 at kickoff."},
    {"stage": "Weeks 11–13", "start": 75, "end": 88, "title": "Finish strong",
     "customer": ["Gets the admin handbook in Supered.",
                  "Final results review: before vs after, what was built, what's still open."],
     "phil": [],
     "architect": ["Adoption check #2 (Day 75), the admin handbook, and the final results review."],
     "ops": [],
     "work": [],
     "done": ["6.04", "6.05", "8.04"]},
    {"stage": "Day 85–90", "start": 85, "end": 90, "title": "Close the program",
     "customer": ["Gets a thank-you, a short feedback survey and a testimonial ask."],
     "phil": ["Reads the feedback."],
     "architect": ["Marks every remaining P1–P8 task Done or Won't do, including the recurring P7 tasks.",
                   "Schedules the monthly dashboard email for the monitoring period."],
     "ops": ["Archives the Supered plan."],
     "work": ["Portfolio Sync moves Current section to P9 once the Target end date passes."],
     "done": ["8.05", "7.01", "7.02", "7.03", "7.04", "7.05", "7.06", "7.07"],
     "note": "In the example, Day 90 is Sunday, Jan 31. Close out by Friday, Jan 29."},
    {"stage": "After: months 1–6", "start": 90, "end": 270, "title": "Free KPI monitoring",
     "customer": ["Gets a monthly KPI snapshot email with 3 short notes.",
                  "Hears from us if something breaks (deliverability drop, workflow errors, form submissions falling).",
                  "Can still send requests at $250 each."],
     "phil": [],
     "architect": ["On the 1st of each month: adds the numbers to the KPI snapshot draft and sends it with the dashboard email.",
                   "Acts on health alerts."],
     "ops": [],
     "work": ["KPI Snapshot Drafter runs on the 1st of the month at 9:00 AM."],
     "done": ["9.01", "9.02"]},
    {"stage": "After: months 3, 5, 6", "start": 180, "end": 270, "title": "Check-ins and the paid next step",
     "customer": ["Month 3: a 30-minute check-in.",
                  "Month 5: hears the paid options (team support at $1,670/mo, building internal capacity, one initiative a month).",
                  "Month 6: last check-in. Picks a paid offer, or monitoring ends."],
     "phil": ["Joins the month-5 conversation if useful."],
     "architect": ["Runs all three calls.",
                   "A paid offer becomes a new deal. With no paid offer, sets Current section = Completed."],
     "ops": [],
     "work": ["Once the row is Completed, the customer drops out of every active view."],
     "done": ["9.03", "9.04", "9.05"]},
]

STATUS_RULES = [
    ("Not started", "Default when the Task Generator copies the task in."),
    ("In progress", "Someone has started it. Move it the day you start."),
    ("Waiting on client", "Blocked on the customer: access, DNS, content or an answer. The Delay Flagger chases after 3 days."),
    ("In review", "Built and waiting for the customer's sign-off."),
    ("Done", "The definition of done is met and checked. The Architect marks client-owned tasks Done once verified. Recurring tasks are marked Done at close-out."),
    ("Won't do", "Doesn't apply to this customer, such as an optional measure they didn't buy or an Enterprise-only item for a Pro customer. Add a note saying why."),
]

REQUEST_FLOW = [
    ("Customer asks", "By email, Slack, in office hours or in Supered."),
    ("Logged the same day", "The Architect adds a Requests row: Customer, Request, Type = Client request, Logged on = today."),
    ("Agent triage", "Request Triage sets Urgency, Price and Due date. A Critical request alerts the Architect and Phil."),
    ("Customer confirms", "The Architect checks the triage, then tells the customer the class, turnaround and price. Paid requests wait for their OK. Fixing something we built never does."),
    ("Work", "New → In progress once they say yes → Done. Bigger than about 2 hours → Quoted → a proposal. An idea for later → Parked."),
    ("Billing", "Suggested: Ops bills every Done request with a price at the end of the month."),
    ("What we find ourselves", "Issues the Architect finds are logged as Issue found, ideas as Client idea. Both feed the Friday update and the what's next call."),
]

WEEKLY_RHYTHM = [
    ("Every day, 6:00 AM", "HubSpot Work", "Portfolio Sync updates Current section and Next due task."),
    ("Weekdays, 8:00 AM", "HubSpot Work", "Delay Flagger messages the Architect about overdue or stuck tasks."),
    ("Monday", "Architect", "Plans the week from My tasks and This week, and moves tasks to In progress."),
    ("Any day", "Customer", "Books office hours and sends requests."),
    ("Any day", "Architect", "Logs requests the day they arrive."),
    ("Once a week", "Phil + Architects", "Delivery review: Health board, Overdue view, Capacity report."),
    ("Thursday, 9:00 AM", "HubSpot Work", "Weekly Update Drafter writes each customer's draft."),
    ("Friday", "Architect", "Adds the numbers, sends the update, marks it Sent and sets Health."),
]

EXCEPTIONS = [
    ("The customer is slow with access or the intake", "Task goes to Waiting on client. Chase on Day 3. On Day 7, escalate to Phil using the escalation path and set Health to At risk."),
    ("A pre-sale item is missing at handoff", "The Architect flags it on the P0 task. Phil fixes it within 24 hours."),
    ("The customer wants to pause", "Set Health to Off track with a note. If the pause is longer than 2 weeks, move the Start date forward by the pause length. The Task Generator re-dates every task."),
    ("The Architect changes", "Change the Architect on the Customers row. The Task Generator moves the open Architect tasks to the new person."),
    ("The program length changes", "Change Program length (60, 75 or 90). Every due date recalculates."),
    ("A due date lands on a weekend or holiday", "Dates are calendar days, so treat it as the next business day. In the example, Day 24 is Thanksgiving, Day 53 is Christmas and Day 60 is New Year's Day."),
    ("Something live breaks", "Log it as a Critical request. Fix it within 1 business day. It's free if it's in something we built."),
    ("The customer wants to buy more mid-program", "Log a request. It becomes Quoted, then a deal. This program's tasks don't change."),
    ("The customer buys another hub mid-program", "Add it to Products purchased and tick Create tasks. The Task Generator adds only that hub's tasks, dated from that day. Core tasks aren't duplicated."),
]
