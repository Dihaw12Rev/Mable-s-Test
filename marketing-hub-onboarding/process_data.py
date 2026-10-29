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
    ("Program length", "60 to 90 days.", "The plan is laid out for 90 days. Each customer project has a Program length; later due dates compress to fit 60 or 75 days."),
    ("Hub tiers", "Marketing Hub Professional and Enterprise.", "Starter removed. Setup items are tagged 'Pro & Ent' or 'Ent only'."),
    ("Strategy lead", "Phil leads through the sale, then the Architect takes over.", "Architect owns MBRs, weekly updates, strategy and the 'what's next' call after the handoff. Phil reviews the next-phase options."),
    ("Picking the Architect", "Phil decides, based on capacity.", "Capacity report in the Onboarding Portfolio (active customers per Architect)."),
    ("HubSpot Work beta", "Enrolled.", "Build in HubSpot Work now."),
    ("Where onboarding lives", "Only in HubSpot Work.", "No Projects pipeline and no tickets for onboarding. Tasks, board and requests all live in Work."),
    ("Client-facing place", "Supered.", "No HubSpot customer portal. Everything the customer sees is in Supered."),
    ("Progress measures (Factories)", "Use the suggestion.", "Standard set added: 0.1, 1.1, 1.2, 1.3 for every customer; 1.0 and 2.1 when bought."),
    ("$250 requests", "Per request. Urgency classes not defined yet.", "Recommended classes added: Critical, High, Standard, Not now."),
    ("Migrations & website work", "In scope.", "Migration and website tasks added to Foundations and Build & launch, with suggested limits."),
    ("Post-program offers", "Free for 6 months. Contents not defined yet.", "Suggested contents for the free KPI monitoring and the three paid offers."),
    ("'What's next' call", "The Architect runs it.", "Tasks 8.02, 8.03 and 9.04 owned by the Architect; Phil reviews the options in 8.01."),
    ("Suggestions from review", "Approved: urgency classes, 2-hour request size, migration and website limits, standard progress measures, $1,670/mo Monthly Plan for team support.", "Applied as written."),
    ("Agents", "HubSpot Work can build agents.", "8 agents added. They only draft, fill dates or flag; none sends anything to a customer."),
    ("HubSpot Work limits (found in the build)", "No custom project fields; no links between tables and projects.", "Customer details live on the Customers table, matched to the project by its exact name. Due date uses two helper columns that the Date Setter agent fills."),
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
     "exit": "Architect assigned, Phil↔Architect 1:1 done, customer project created, kickoff booked."},
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
    ("0.05", "P0", "Products and quote on the deal", "Pricing calculator used, line items added, quote created. Hub tier is Pro or Enterprise.", "Phil", "No", -14, -10, "0.04", "Deal line items + quote", ""),
    ("0.06", "P0", "Progress measures picked", "Core set (0.1, 1.1, 1.2, 1.3) plus any optional ones bought (1.0, 2.1). Baselines noted if known.", "Phil", "No", -14, -7, "0.05", "Deal note", ""),
    ("0.07", "P0", "POC and supporters identified", "Contacts on the deal with labels (POC, Supporter, Billing, Decision maker). POC gets the weekly email.", "Phil", "Yes", -10, -3, "0.05", "Deal contacts", ""),
    ("0.08", "P0", "Agreement signed", "Includes AI terms, escalation path, how progress is measured, POC and supporters, strategic job → tactical outcomes → progress measures, and request handling ($250 per request, urgency classes).", "Client POC", "Yes", -5, 0, "0.07", "Quote / e-signature", ""),

    # P1 — Close & welcome
    ("1.01", "P1", "Pick the Architect", "Phil checks the Capacity report (active customers per Architect) and picks the Architect.", "Phil", "No", 0, 1, "0.08", "Work: Capacity report", ""),
    ("1.02", "P1", "Create the customer project", "Duplicate the 'Marketing Hub Onboarding (Template)' project and name it exactly '<Client> · Marketing Hub Onboarding'. Add a Customers row with that exact name plus Company, Deal, Architect, Program length and Start date. Share the project with the Architect.", "Ops", "No", 0, 1, "1.01", "Work: customer project + Customers row", ""),
    ("1.03", "P1", "Welcome email #1: welcome + Action Plan", "Sent from Phil on Day 0: Supered Action Plan link, kickoff booking link, first to-dos (grant HubSpot access, fill the intake form).", "Ops", "Yes", 0, 0, "0.08", "HubSpot email (automated on deal stage)", ""),
    ("1.04", "P1", "Build the Supered Action Plan", "Duplicate the Marketing Hub Action Plan template; add the agreement, FigJam, client to-dos and access checklist.", "Ops", "Yes", 0, 1, "1.02", "Supered", ""),
    ("1.05", "P1", "Phil ↔ Architect handoff (30 min)", "Walk through FigJam, customer context, products, the From→To goal, progress measures and KPIs, schedule. Architect checks the Handoff checklist section. Strategy lead moves to the Architect after this call.", "Phil", "No", 1, 3, "1.01", "Meeting on the deal", ""),
    ("1.06", "P1", "Set up progress measures", "Add the customer's progress measures to the project (name '<Client> 1.1 Visitor to Lead' etc.) with baseline, target and schedule.", "Architect", "No", 1, 3, "1.05", "Work: customer project", ""),
    ("1.07", "P1", "Office hours booking link", "Architect's HubSpot meetings link (office-hours type) added to the Supered plan.", "Architect", "Yes", 1, 2, "1.01", "HubSpot Meetings + Supered", ""),
    ("1.08", "P1", "Welcome email #2: how we work", "Day 2: office hours, Friday updates, how to send a request and the urgency classes, escalation path, how we use AI.", "Ops", "Yes", 2, 2, "1.03", "HubSpot email (automated)", ""),
    ("1.09", "P1", "Kickoff booked", "Client books the 15-minute kickoff from welcome email #1. Chase on Day 3 if not booked.", "Client POC", "Yes", 0, 5, "1.03", "HubSpot Meetings", ""),

    # P2 — Access & intake
    ("2.01", "P2", "HubSpot access granted", "Partner access or a Super Admin user for the Architect. Confirm Pro or Enterprise per hub.", "Client POC", "Yes", 1, 3, "1.03", "Supered to-do", ""),
    ("2.02", "P2", "Intake form submitted", "Short form with only what pre-sale didn't capture (Intake Form tab).", "Client POC", "Yes", 1, 5, "1.03", "Intake form", ""),
    ("2.03", "P2", "Access to connected systems", "DNS/IT contact, website CMS, GA4/GTM, ad accounts, social accounts, and the old email/marketing tool we migrate from.", "Client POC", "Yes", 1, 7, "2.02", "Supered to-do", ""),
    ("2.04", "P2", "Brand & content assets shared", "Brand guide, logos, fonts, colors, email templates, key content, lists to import.", "Client POC", "Yes", 1, 7, "2.02", "Supered upload", ""),
    ("2.05", "P2", "Supered announcement to POC", "Short video: how Supered works (Bases, announcements, documentation) and where updates show up.", "Architect", "Yes", 2, 3, "1.04", "Supered", ""),
    ("2.06", "P2", "Portal audit", "Data health, email health, existing assets, tracking, workflows, properties, old tool inventory. 1-page summary for kickoff.", "Architect", "No", 3, 7, "2.01", "Work: customer project (notes)", ""),
    ("2.07", "P2", "Baseline numbers", "Record the 'before' number for each progress measure.", "Architect", "No", 5, 7, "2.06", "Work: customer project", ""),

    # P3 — Kickoff
    ("3.01", "P3", "Kickoff agenda", "Plan summary, missing items, decisions needed. Drafted from intake + audit.", "Architect", "No", 5, 7, "2.02, 2.06", "Work: customer project (notes)", ""),
    ("3.02", "P3", "Kickoff session (15 min)", "Architect & team intro; confirm the goal and plan; walk through missing items; explain office hours, Friday updates, MBRs and how to send requests.", "Architect", "Yes", 5, 10, "3.01", "Meeting", ""),
    ("3.03", "P3", "Book MBRs and the 'what's next' call", "MBR #1 ≈ Day 30, MBR #2 ≈ Day 60, 'what's next' ≈ Day 60–65, final results review ≈ Day 85 (scaled to program length).", "Architect", "Yes", 5, 10, "3.02", "Meetings", ""),
    ("3.04", "P3", "Kickoff recap within 24h", "Decisions, owners, dates, client to-dos. Supered plan updated.", "Architect", "Yes", 6, 11, "3.02", "Email + Supered", ""),

    # P4 — Foundations
    ("4.01", "P4", "Account, users & security", "Users, permission sets, 2FA; Enterprise extras where bought.", "Architect", "No", 7, 12, "2.01", "Tech Setup tab", ""),
    ("4.02", "P4", "Tracking & consent", "Tracking code on every domain, internal traffic excluded, cookie banner set.", "Architect", "No", 7, 14, "2.03", "Tech Setup tab", ""),
    ("4.03", "P4", "Domains & email authentication", "Content domain connected; sending domain authenticated (SPF, DKIM, DMARC) with the client's DNS contact.", "Architect", "No", 7, 18, "2.03", "Tech Setup tab", ""),
    ("4.04", "P4", "Email foundations", "Subscription types, footer and address, brand kit, email templates, default sender.", "Architect", "No", 10, 18, "2.04", "Tech Setup tab", ""),
    ("4.05", "P4", "Data model", "Property audit, lifecycle stage definitions, lead status, marketing-contact rules.", "Architect", "No", 10, 21, "2.06", "Tech Setup tab", ""),
    ("4.06", "P4", "Migration plan & export", "Inventory and export from the old tool: lists, consent, unsubscribes and bounces, templates, active automations.", "Architect", "No", 8, 16, "2.03", "Tech Setup tab", ""),
    ("4.07", "P4", "Data import & cleanup", "Import contacts/companies (including migrated lists with consent mapped and unsubscribes suppressed), dedupe, associations, marketing contacts.", "Architect", "No", 14, 25, "4.05, 4.06", "Tech Setup tab", ""),
    ("4.08", "P4", "Website connection", "HubSpot forms, CTAs, chat and meetings on the current website; landing page and blog templates.", "Architect", "No", 14, 28, "4.02", "Tech Setup tab", ""),
    ("4.09", "P4", "Integrations", "GA4, ad accounts, social, webinar tool, Slack, CRM sync if their CRM isn't HubSpot.", "Architect", "No", 14, 28, "2.03", "Tech Setup tab", ""),
    ("4.10", "P4", "Baseline dashboard", "One report per progress measure, showing baseline vs now. Used in every weekly update.", "Architect", "Yes", 18, 28, "2.07", "HubSpot dashboard", ""),
    ("4.11", "P4", "Foundation QA", "Test visit → form → contact → email → notification end to end; test email rendering and deliverability.", "Architect", "No", 25, 30, "4.02, 4.03, 4.04, 4.07", "Tech Setup tab", ""),
    ("4.12", "P4", "Supered video: foundations done", "What changed for the customer and why it matters.", "Architect", "Yes", 28, 30, "4.11", "Supered", ""),

    # P5 — Build & launch (one task per progress measure + launch tasks)
    ("5.01", "P5", "Build 1.1 Visitor → Lead", "Forms, CTAs, landing and thank-you pages live on the right pages. Measure: visit-to-contact rate.", "Architect", "No", 21, 40, "4.08, 4.11", "Progress measure 1.1", ""),
    ("5.02", "P5", "Build 1.2 Lead → MQL", "Segments, nurture emails and workflows, lead scoring, lifecycle automation. Client approves copy. Measure: lead-to-MQL rate.", "Architect", "Yes", 30, 55, "5.01, 4.07", "Progress measure 1.2", ""),
    ("5.03", "P5", "Build 1.3 MQL → Meeting", "MQL definition agreed with sales, owner assignment, notifications, follow-up SLA, meetings link in nurture. Measure: MQL-to-meeting rate.", "Architect", "Yes", 35, 60, "5.02", "Progress measure 1.3", ""),
    ("5.04", "P5", "Build 2.1 Subscriber → Engaged (if bought)", "Newsletter or content program, subscription preferences, re-engagement and sunset flows. Measure: email click rate, engaged contacts.", "Architect", "No", 35, 60, "4.04", "Progress measure 2.1", ""),
    ("5.05", "P5", "Build 1.0 Stranger → Visitor (if bought)", "Campaigns and UTMs, ad audiences and conversion events, social publishing, SEO recommendations. Measure: sessions by source.", "Architect", "No", 30, 60, "4.09", "Progress measure 1.0", ""),
    ("5.06", "P5", "Migration: rebuild and switch off old tool", "Rebuild templates and active automations from the old tool, send in parallel once, then switch the old tool off.", "Architect", "Yes", 25, 50, "4.06, 4.07", "Tech Setup tab", ""),
    ("5.07", "P5", "Website: landing pages & blog", "Migrate landing pages and blog posts within the agreed limit; redirects set.", "Architect", "Yes", 30, 60, "4.08", "Tech Setup tab", ""),
    ("5.08", "P5", "First campaign live", "Campaign with UTMs and assets, launched with the client.", "Architect", "Yes", 40, 65, "5.01, 5.02", "HubSpot campaigns", ""),
    ("5.09", "P5", "Performance reporting", "Marketing performance dashboard and funnel by progress measure; revenue attribution on Enterprise.", "Architect", "Yes", 45, 70, "4.10", "HubSpot dashboard", ""),
    ("5.10", "P5", "AI / Breeze setup", "Brand voice and content tools, only within the AI terms in the agreement.", "Architect", "No", 45, 70, "4.04", "Tech Setup tab", ""),
    ("5.11", "P5", "Client sign-off per progress measure", "Client approves each build before it goes live.", "Client POC", "Yes", 35, 75, "5.01–5.07", "Work: Status 'In review'", ""),
    ("5.12", "P5", "Supered video per delivery", "What was built, how to use it, why it matters.", "Architect", "Yes", 35, 75, "5.11", "Supered", "After each delivery"),

    # P6 — Training & adoption
    ("6.01", "P6", "Confirm training plan", "Who needs which modules (Training tab), from the intake.", "Architect", "Yes", 10, 14, "2.02", "Training tab", ""),
    ("6.02", "P6", "Deliver training modules", "Supered videos + practice in office hours, timed to when each feature ships.", "Architect", "Yes", 14, 85, "6.01", "Supered + office hours", ""),
    ("6.03", "P6", "Adoption check #1", "Logins, emails sent, workflows active, dashboards viewed. Flag low adoption in the weekly update.", "Architect", "No", 45, 45, "6.02", "Work: customer project", ""),
    ("6.04", "P6", "Admin handbook (Supered Base)", "How the portal is set up: naming, properties, workflows, who owns what.", "Architect", "Yes", 60, 85, "5.11", "Supered Base", ""),
    ("6.05", "P6", "Adoption check #2", "Same check before the final results review.", "Architect", "No", 75, 75, "6.03", "Work: customer project", ""),

    # P7 — Run cadence (recurring)
    ("7.01", "P7", "Office hours", "Bookable slots for questions, coaching and training practice.", "Architect", "Yes", 7, 90, "1.07", "HubSpot Meetings", "Weekly"),
    ("7.02", "P7", "Weekly update", "Drafted with AI, reviewed and sent by the Architect: work done and the strategic issue it moves, numbers vs baseline, issues found outside scope, next week, client to-dos.", "Architect", "Yes", 7, 90, "4.10", "Email, logged on the deal", "Weekly (Friday)"),
    ("7.03", "P7", "Handle requests by urgency", "Every request gets logged with an urgency class and handled in that time ($250 per request; see Request Classes).", "Architect", "Yes", 7, 90, "", "Work: Requests table", "As they come in"),
    ("7.04", "P7", "Log issues and 'not now' ideas", "Out-of-scope issues and client ideas go to the Requests table as 'Not now', to sell later.", "Architect", "No", 7, 90, "", "Work: Requests table", "As they come in"),
    ("7.05", "P7", "Health check", "Set Health (On track / At risk / Off track) and blockers. Escalate per the escalation path.", "Architect", "No", 7, 90, "", "Work: Customers row (Health)", "Weekly"),
    ("7.06", "P7", "Monthly Business Review", "Progress vs baseline, numbers trend, issues and opportunities. Architect leads; Phil optional.", "Architect", "Yes", 30, 60, "3.03", "Meeting", "Monthly"),
    ("7.07", "P7", "Internal delivery review", "Phil + Architects: at-risk customers, capacity, blockers.", "Phil", "No", 7, 90, "", "Work: Portfolio", "Weekly"),

    # P8 — What's next
    ("8.01", "P8", "Prep next-phase options", "Results so far, issues found and 'not now' list → Option A and Option B. Phil reviews before the call.", "Architect", "No", 55, 60, "7.04", "Work: customer project (notes)", ""),
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
]

# Standard progress measures (Factories). Naming follows the existing records: "<Client> 1.1 Visitor to Lead".
# id, name, when, what it measures, HubSpot report, built by
FACTORIES = [
    ("0.1", "Database → Marketable database", "Every customer", "% of contacts with lifecycle stage and original source set; marketable contacts; bounce rate under 2%.", "Contacts by lifecycle stage; email health", "4.05, 4.06, 4.07"),
    ("1.1", "Visitor → Lead", "Every customer", "Visit-to-contact conversion rate; new contacts from forms per month.", "Sessions vs new contacts by source", "5.01, 4.08"),
    ("1.2", "Lead → MQL", "Every customer", "Lead-to-MQL rate; MQLs per month.", "Lifecycle stage funnel", "5.02"),
    ("1.3", "MQL → Meeting", "Every customer", "MQL-to-meeting rate; time to first sales touch.", "Funnel + meetings booked by source", "5.03"),
    ("1.0", "Stranger → Visitor", "When ads, SEO or content is bought", "Sessions per month by source.", "Traffic analytics by source", "5.05"),
    ("2.1", "Subscriber → Engaged", "When email programs are bought", "Email click rate; contacts engaged in the last 90 days.", "Email performance; engagement segment size", "5.04"),
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
    ("High", "Needed for a launch or deadline in the next 2 weeks.", "Started within 2 business days; done within 5.", "$250"),
    ("Standard", "A small new request with no hard deadline.", "Planned into next week; done within 10 business days.", "$250"),
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
]

# area, item, details, tier ("Pro & Ent" or "Ent only"), task id, owner
TECH_SETUP = [
    ("Account", "Users & permission sets", "Invite client users, set permissions by role, teams if needed.", "Pro & Ent", "4.01", "Architect"),
    ("Account", "Require 2FA", "For every user.", "Pro & Ent", "4.01", "Architect"),
    ("Account", "Single sign-on (SSO)", "If the client uses an identity provider.", "Ent only", "4.01", "Architect"),
    ("Account", "Brands / business units", "If they market more than one brand.", "Ent only", "4.01", "Architect"),
    ("Account", "Sandbox account", "Test workflows and changes before production.", "Ent only", "4.01", "Architect"),
    ("Tracking", "Tracking code on every domain", "CMS plugin or GTM. Verify with a test visit.", "Pro & Ent", "4.02", "Architect"),
    ("Tracking", "Exclude internal traffic", "Client and RevGravy IPs/domains.", "Pro & Ent", "4.02", "Architect"),
    ("Tracking", "Cookie consent banner", "Per the regions in the intake.", "Pro & Ent", "4.02", "Architect"),
    ("Domains", "Connect content domain", "Landing pages / blog subdomain (e.g. go.client.com).", "Pro & Ent", "4.03", "Architect"),
    ("Domains", "Email sending domain authentication", "SPF, DKIM, DMARC added by the client's DNS contact; verified in HubSpot.", "Pro & Ent", "4.03", "Architect + client IT"),
    ("Email", "Subscription types", "Per content type; mapped to consent rules.", "Pro & Ent", "4.04", "Architect"),
    ("Email", "Footer, address, default sender", "Compliant footer, real sender name.", "Pro & Ent", "4.04", "Architect"),
    ("Email", "Brand kit & email templates", "Logo, colors, fonts; 2–3 reusable templates.", "Pro & Ent", "4.04", "Architect"),
    ("Data", "Property audit", "Remove unused, add what the progress measures need. Naming convention documented.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Lifecycle stages & lead status", "Definitions agreed with the client; automation set.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Marketing contact rules", "Who is a marketing contact; keeps billing under control.", "Pro & Ent", "4.05", "Architect"),
    ("Data", "Custom behavioral events", "Track key product or site actions.", "Ent only", "4.05", "Architect"),
    ("Migration", "Old tool inventory", "Lists, segments, templates, active automations, integrations.", "Pro & Ent", "4.06", "Architect"),
    ("Migration", "Export lists with consent", "Including unsubscribes and hard bounces to suppress.", "Pro & Ent", "4.06", "Architect"),
    ("Data", "Import contacts & companies", "Mapped import, consent mapped, unsubscribes suppressed, dedupe, associations.", "Pro & Ent", "4.07", "Architect"),
    ("Data", "Data hygiene workflows", "Formatting, required fields, duplicates.", "Pro & Ent", "4.07", "Architect"),
    ("Website", "HubSpot forms on the site", "Replace or collect existing site forms.", "Pro & Ent", "4.08", "Architect"),
    ("Website", "CTAs, chat & meetings on the site", "Placed on the pages that matter.", "Pro & Ent", "4.08", "Architect"),
    ("Website", "Landing page & blog templates", "Matching the brand kit.", "Pro & Ent", "4.08", "Architect"),
    ("Integrations", "GA4", "Connected for reporting.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Ad accounts", "Google, Meta, LinkedIn with conversion events.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Social accounts", "Connected for publishing and reporting.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "Webinar, Slack, other apps", "As listed in the intake.", "Pro & Ent", "4.09", "Architect"),
    ("Integrations", "CRM sync (if CRM isn't HubSpot)", "Field mapping, sync rules, lifecycle alignment.", "Pro & Ent", "4.09", "Architect"),
    ("Reporting", "Baseline dashboard", "One report per progress measure; baseline vs now.", "Pro & Ent", "4.10", "Architect"),
    ("QA", "End-to-end test", "Visit → form → contact → workflow → email → notification.", "Pro & Ent", "4.11", "Architect"),
    ("Lead capture", "Forms, CTAs, landing & thank-you pages", "Per offer.", "Pro & Ent", "5.01", "Architect"),
    ("Segmentation", "Core segments", "Persona, lifecycle, engagement, customers, suppression.", "Pro & Ent", "5.02", "Architect"),
    ("Automation", "Nurture workflows & emails", "Per persona / offer.", "Pro & Ent", "5.02", "Architect"),
    ("Automation", "Lead scoring", "Fit + engagement score; MQL threshold.", "Pro & Ent", "5.02", "Architect"),
    ("Automation", "MQL handoff", "Assignment, notifications, follow-up SLA.", "Pro & Ent", "5.03", "Architect"),
    ("Email", "Re-engagement & sunset flows", "Keeps the list healthy.", "Pro & Ent", "5.04", "Architect"),
    ("Campaigns", "Campaigns, UTMs & ad audiences", "Campaign object, UTM conventions, retargeting audiences.", "Pro & Ent", "5.05", "Architect"),
    ("Migration", "Rebuild templates & automations", "Up to 5 templates; automations active today.", "Pro & Ent", "5.06", "Architect"),
    ("Migration", "Parallel send, then switch off the old tool", "One parallel send to compare, then cancel the old tool.", "Pro & Ent", "5.06", "Architect + Client POC"),
    ("Website", "Migrate landing pages & blog", "Up to 10 landing pages + blog import; redirects set.", "Pro & Ent", "5.07", "Architect"),
    ("Reporting", "Marketing performance dashboard", "Traffic, leads, MQLs, emails, campaigns.", "Pro & Ent", "5.09", "Architect"),
    ("Reporting", "Revenue attribution reports", "Multi-touch attribution.", "Ent only", "5.09", "Architect"),
    ("AI", "Breeze / AI settings", "Brand voice and content tools within the agreed AI terms.", "Pro & Ent", "5.10", "Architect"),
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
    ("Request log with urgency", (2, "Requests table in each project"), (0, "Not its job"), (2, "Ticket pipeline")),
    ("Maturity", (0, "Public beta"), (2, "Generally available"), (2, "Generally available")),
]

WHERE_IT_LIVES = [
    ("HubSpot Work", "The whole onboarding: a template project copied per customer (tasks by section, board, timeline, requests) and a Customers table where each customer's details live."),
    ("Supered", "Everything the customer sees: Action Plan, announcements, delivery and training videos, admin handbook."),
    ("HubSpot CRM", "The deal-stage gate, the two welcome emails, meetings links and the dashboards that report progress measures."),
    ("Not used for onboarding", "Projects object pipelines, tickets, HubSpot customer portal, Trello."),
]

# HubSpot Work structure — used by the sheet and both prompts.
# Built and checked in the portal (Oct 2026). HubSpot Work has no custom project fields and no table-to-project
# links, so customer details live on the Customers table, and the Customer column holds the exact project name.
WORK_STATUSES = ["Not started", "In progress", "Waiting on client", "In review", "Done", "Won't do"]
WORK_TASK_COLUMNS = [
    ("Task ID", "Text", "e.g. 4.03. First column, so 'Depends on' can be read"),
    ("Task", "Text", "Task name"),
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
    ("Project Day 0", "Date", "Helper for the formula: same date on every row, filled per customer (hidden)"),
    ("Program length", "Number", "Helper for the formula: 60, 75 or 90 on every row, filled per customer (hidden)"),
]
WORK_VIEWS = [
    ("Board", "Columns = Status. Cards show Task ID, Task, Assignee, Due date."),
    ("By section", "List grouped by Section (P0 → P9), sorted by Task ID."),
    ("Timeline", "Start date → Due date, grouped by Section."),
    ("Calendar", "By Due date."),
    ("My tasks", "Assignee = me, Status not Done / Won't do."),
    ("Client to-dos", "Owner role = Client POC, Status not Done."),
    ("This week", "Due date in the next 7 days, Status not Done."),
    ("Overdue", "Due date before today, Status not Done / Won't do."),
]
WORK_REQUEST_COLUMNS = [
    ("Request", "Text"), ("Urgency", "Dropdown: Critical, High, Standard, Not now"),
    ("Type", "Dropdown: Client request, Issue found, Client idea"), ("Status", "Dropdown: New, Quoted, In progress, Done, Parked"),
    ("Price", "Number (default 250)"), ("Logged on", "Date"), ("Due date", "Date"), ("Notes", "Long text"),
]
WORK_PORTFOLIO_COLUMNS = [
    ("Customer", "Text: the customer project's exact name, '<Client> · Marketing Hub Onboarding'"),
    ("Company", "CRM company"), ("Deal", "CRM deal"), ("Architect", "HubSpot user"),
    ("Program length", "Number: 60, 75 or 90"), ("Start date", "Date (Day 0)"), ("Target end date", "Date"),
    ("Marketing Hub tier", "Dropdown: Professional, Enterprise"), ("Health", "Dropdown: On track, At risk, Off track"),
    ("Current section", "Dropdown: P0–P9, Completed"), ("Next MBR", "Date"), ("Next due task", "Text"),
    ("From→To goal", "Long text"), ("FigJam link", "URL"), ("Supered Action Plan link", "URL"),
]
WORK_PORTFOLIO_VIEWS = [
    ("Capacity", "Report: active customers per Architect (a report, since saved views can't count). Phil uses it to pick the Architect."),
    ("Health board", "Columns = Health."),
    ("Ending soon", "Target end date in the next 35 days (time for the 'what's next' call)."),
]

# How a new customer gets set up, given those platform limits.
NEW_CUSTOMER_STEPS = [
    "Duplicate 'Marketing Hub Onboarding (Template)' and name the copy exactly '<Client> · Marketing Hub Onboarding'.",
    "Add a row to Customers with Customer = that exact name, plus Company, Deal, Architect, Program length, Start date and the rest.",
    "The Date Setter agent fills Project Day 0 and Program length on every task in the copy, so Due dates calculate. Without the agent, bulk-edit those two columns on all rows.",
    "Share the copy with the Architect (workspaces are private by default).",
]

# HubSpot Work agents. Every agent only drafts, fills dates or flags; none sends anything to a customer.
# Agents find a customer's project through the Customers row: its Customer value is the project's exact name.
# name, trigger, what it does
WORK_AGENTS = [
    ("Date Setter", "A Customers row's Start date, Program length or Architect is set or changed",
     "Find the project whose name matches the row's Customer value. In its Tasks table, set Project Day 0 = the row's Start date and Program length = the row's Program length on every task, so the Due date formula calculates. Assign every task with Owner role 'Architect' to the row's Architect. Set the row's Target end date = Start date + Program length."),
    ("Handoff Brief", "A new row in Customers",
     "Read the linked deal's history, notes, meetings and emails. Write a one-page brief for the Architect: who the customer is, the From→To goal, what they bought, the progress measures, the people involved, risks and open questions. Save it in the matching customer project and notify the Architect."),
    ("Weekly Update Drafter", "Every Thursday, for each Customers row whose Current section is P2 to P8",
     "In the matching project, draft the Friday update in five parts: 1) work done this week and the strategic issue it moves, 2) numbers vs baseline, 3) issues found outside scope, 4) next week, 5) client to-dos. Use tasks marked Done this week, tasks due next week, and Requests logged this week. Save the draft in the project and notify the Architect, who reviews and sends it."),
    ("Delay Flagger", "Every weekday morning",
     "In each customer project, flag tasks past their Due date and tasks 'Waiting on client' for more than 3 days. If a project has 3 or more overdue tasks, set Health to At risk on its Customers row. Notify the Architect, and notify Phil when Health becomes At risk or Off track."),
    ("Request Triage", "A new row in a customer project's Requests table",
     "Suggest the Urgency class and Price from the urgency rules, and set Due date from that class's turnaround. If it looks bigger than about 2 hours of work, mark it 'Quoted' and say why. Notify the Architect at once for Critical requests."),
    ("Portfolio Sync", "Every day",
     "For each Customers row, look at the matching project and update Current section (earliest section with open tasks), Next MBR and Next due task."),
    ("What's Next Prep", "35 days before a Customers row's Target end date",
     "Summarize results vs baseline, issues found and 'not now' requests into Option A and Option B for the next phase. Save it in the matching project, notify the Architect, and ask Phil to review before the call."),
    ("KPI Snapshot Drafter", "Monthly for 6 months after a Customers row's Target end date",
     "Draft the monthly KPI snapshot notes (3 short notes on the progress measures) for the Architect to review and send with the dashboard email."),
]

OPEN_QUESTIONS = []
