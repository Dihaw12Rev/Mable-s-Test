"""Build RevGravy_Customer_Onboarding_SOP.pdf (and its source sop.html) from process_data.py.

Run:  python3 build_sop_pdf.py && node render_pdf.js
"""
import html
import json
from collections import defaultdict
from pathlib import Path

import process_data as d

HERE = Path(__file__).parent
OUT_HTML = HERE / "sop.html"
E = html.escape
VERSION_DATE = "November 2026"

PHASE = {p["id"]: p for p in d.PHASES}
MODULE_LABEL = {"Core": "Core", "MH": "Marketing", "SH": "Sales", "SV": "Service"}
count = {m: sum(1 for t in d.TASKS if d.module_of(t[0]) == m) for m in d.MODULES}


def days(s, e):
    if e < 0:
        return "Before Day 0"
    return f"Day {s}" if s == e else f"Day {s}–{e}"


def ul(items):
    return "<ul>" + "".join(f"<li>{E(i)}</li>" for i in items) + "</ul>"


# ---------------------------------------------------------------- procedure
STEPS = [
    {"n": 1, "title": "Prepare the sales handoff", "when": "Before Day 0 · P0", "who": ["Phil"],
     "do": ["Write the research brief from the company website and attach it to the deal.",
            "Build the FigJam canvas after the Fit call: strategic motivation, tactical outcomes, progress measures, fee range.",
            "Write the From→To statement: one sentence from where they are to where they want to be.",
            "Get the tech stack and team capacity survey back from the customer.",
            "Put products, quote and hub tiers on the deal. Every hub sold is Professional or Enterprise.",
            "Pick the progress measures for each hub sold (Appendix B), with baselines where known.",
            "Confirm the POC, supporters and decision maker from contact labels or explicit conversations. Never infer authority from a billing label or a job title.",
            "Get the agreement signed: AI terms, escalation path, how progress is measured, $250 requests with urgency classes."],
     "done": "There is documented authority to start, scope is understood, and every missing item has a named owner. Missing evidence can carry into onboarding, but it stays visibly open."},
    {"n": 2, "title": "Pick the Architect and add the customer", "when": "Day 0 · payment received", "who": ["Phil", "Ops"],
     "do": ["Phil opens the Capacity report (active customers per Architect) and picks the Architect.",
            "Ops adds one Customers row within 4 business hours: Customer, Company, Deal, Architect, Program length (60, 75 or 90), Start date, Products purchased, Hub tiers, From→To goal, FigJam and Supered links.",
            "Start date is Day 0: the day the deal reached Start Payment Received. It is never the kickoff date.",
            "Leave unknown values blank and create a follow-up task. Blank beats invented.",
            "Ops ticks Create tasks.",
            "Welcome email #1 goes out from Phil: the Supered Action Plan, the kickoff booking link and the first to-dos."],
     "done": "The Customers row is complete, the Company and Deal are linked, and Create tasks is ticked."},
    {"n": 3, "title": "Create the customer's tasks", "when": "Day 0", "who": ["HubSpot Work", "Ops"],
     "do": ["The Onboarding Task Generator copies the Onboarding Library once, plus one library per product purchased, into Customer Task.",
            "It fills each task's Project Day 0 and Program length so the Due date formula calculates, and assigns the Architect's tasks.",
            "It sets Target end date, adds the products to Tasks created for, and unticks Create tasks.",
            f"Ops checks the count: Core {count['Core']}, plus Marketing {count['MH']}, Sales {count['SH']}, Service {count['SV']}.",
            "If the tasks don't appear within 15 minutes, Ops copies them from the libraries by hand and fills the same fields."],
     "done": "Tasks created for lists every product purchased, and the task count matches."},
    {"n": 4, "title": "Run the internal handoff", "when": "Days 1–3", "who": ["Phil", "Architect"],
     "do": ["Read the Handoff Brief in the Update table. It's written from the deal's history; correct anything that's wrong before the call.",
            "Hold a 30-minute handoff call: what was bought, the outcome, baselines and targets, people and decision path, access needs, risks, the first customer commitment.",
            "The Architect walks the P0 checklist and marks each item Done only with evidence. Anything missing goes back to Phil, who fixes it within 24 hours.",
            "The Architect sets Won't do, with a reason, on anything the customer didn't buy (optional builds, Enterprise-only items for a Pro customer).",
            "The Architect writes the progress measures with baseline, target, source and owner into the Customers row.",
            "Every unresolved question becomes a linked task with an owner and a date.",
            "From here on, the Architect is the strategy lead."],
     "done": "P0 is closed or every gap is owned, the measures are recorded, and the brief is marked Reviewed."},
    {"n": 5, "title": "Welcome, access and intake", "when": "Days 0–7 · P1–P2", "who": ["Architect", "Ops", "Customer"],
     "do": ["Ops builds the Supered Action Plan from the template for the products bought.",
            "Welcome email #2 goes out on Day 2: office hours, Friday updates, how to send requests and the urgency classes, escalation path, how we use AI.",
            "The customer grants HubSpot access, fills the intake form, shares access to connected systems and old tools, and uploads brand files.",
            "Customer-owned tasks sit in Waiting on client. The Architect marks them Done only once the access works or the form is in. Silence is not access.",
            "Chase on Day 3. On Day 7, escalate to Phil and set Health to At risk.",
            "The Architect runs the portal audit and records baseline numbers.",
            "Credentials live only in the approved secure system, never in task notes."],
     "done": "Access is granted, the intake is in, and baselines are recorded."},
    {"n": 6, "title": "Kickoff", "when": "Days 5–10 · P3", "who": ["Architect", "Customer"],
     "do": ["Draft the agenda from the intake and the audit.",
            "In a 15-minute call: introduce the team; confirm the goal, scope and plan; walk through missing items; explain office hours, Friday updates, MBRs and requests.",
            "Book MBR #1 (about Day 30), MBR #2 (about Day 60), the what's next call (about 30 days before the end) and the final results review. Scale these for 60- and 75-day programs.",
            "Fill Next MBR on the Customers row. Confirm who needs which training modules.",
            "Send the recap within 24 hours and update the Supered plan."],
     "done": "The plan is confirmed, the meetings are on calendars, and the recap is sent."},
    {"n": 7, "title": "Foundations", "when": "Days 7–30 · P4", "who": ["Architect"],
     "do": ["Work through the Core foundation tasks (account, data model, import, integrations, baseline dashboard) and each hub's foundation tasks.",
            "A task is Done when every subtask is ticked or marked not applicable.",
            "Tasks blocked on the customer's IT (DNS, for example) go to Waiting on client.",
            "Foundation QA (4.11): test the main flow end to end for every hub sold.",
            "Record a Supered video: what changed for the customer and why it matters."],
     "done": "Foundation QA passes and the baseline dashboard is live."},
    {"n": 8, "title": "Build and launch", "when": "Days 21–75 · P5–P6", "who": ["Architect", "Customer"],
     "do": ["Build one progress measure at a time, in the order of the hub's library.",
            "A build sits in In review while it waits for the customer's sign-off, and is Done only after sign-off and go-live.",
            "Record a Supered video per delivery, and deliver the matching training module as each feature ships.",
            "Migrations: rebuild, send in parallel once, then switch the old tool off with the customer's confirmation.",
            "Day 45 and Day 75: adoption checks. Attendance alone is not adoption."],
     "done": "Every progress measure sold is live, signed off and reporting."},
    {"n": 9, "title": "Run the weekly rhythm", "when": "Day 7 to the end · P7", "who": ["Architect", "Phil", "HubSpot Work"],
     "do": ["Monday: the Architect plans the week from My tasks and This week.",
            "Every day: review overdue tasks and separate internal delays from Waiting on client.",
            "Friday: send the update in five parts: work done and the strategic issue it moves, numbers vs baseline, issues found outside scope, next week, the customer's to-dos. The Update row goes Draft → Reviewed → Sent.",
            "Set Health weekly from evidence. On track means credible; At risk means a slip is likely but recoverable; Off track means a milestone is already jeopardized.",
            "Phil runs a weekly delivery review with the Architects using the Health board, the Overdue view and the Capacity report.",
            "MBRs compare sourced actuals with baseline and target."],
     "done": "Recurring tasks stay In progress until close-out. Each Sent update is the record that the week happened."},
    {"n": 10, "title": "Handle requests", "when": "Any time", "who": ["Architect", "Customer"],
     "do": [f"{h}: {t.replace('Suggested: ', '')}" for h, t in d.REQUEST_FLOW],
     "done": "Done means the result is verified and communicated, with the customer's validation captured where needed."},
    {"n": 11, "title": "What's next", "when": "About 35 to 25 days before the end · P8", "who": ["Architect", "Phil"],
     "do": ["The Architect prepares Option A and Option B from results, issues found and 'not now' ideas, and Phil reviews them.",
            "The Architect runs the what's next call: results so far, long-term vision, the A/B choice, and the 6 months of free KPI monitoring.",
            "The chosen option becomes a new deal in the Sales Pipeline.",
            "New work is never added silently to the original scope. It goes through a linked request and approval."],
     "done": "The customer has chosen a next step, and the proposal is sent."},
    {"n": 12, "title": "Graduate", "when": "Last week of the program", "who": ["Architect", "Ops"],
     "do": ["Run the final results review: before vs after for every progress measure, what was built, what's still open.",
            "Deliver the admin handbook in Supered.",
            "Check the graduation gate (below). Mark every remaining task Done or Won't do, including the recurring ones.",
            "Send the thank-you, the feedback survey and the testimonial ask. Ops archives the Supered plan.",
            "Set up the monthly dashboard email for the monitoring period."],
     "done": "The graduation gate is met. Health keeps its last value; it is not a completion status."},
    {"n": 13, "title": "After the program", "when": "6 months after the end · P9", "who": ["Architect"],
     "do": ["Monthly: the KPI snapshot email with 3 short notes from the Architect.",
            "Act on portal health alerts: deliverability drops, workflow errors, form submissions falling.",
            "Check-ins at month 3 and month 6. At month 5, present the paid options.",
            "A paid offer becomes a new deal. With no paid offer, set Current section to Completed at month 6."],
     "done": "The customer is on a paid offer, or monitoring has ended cleanly."},
]

GRADUATION_GATE = [
    "Contracted scope is delivered, or explicitly waived with a recorded reason.",
    "Customer acceptance is captured where required.",
    "Training is complete, and the customer knows how to get support.",
    "Every progress measure has a final value from a real source and a continuing owner.",
    "Critical blockers are resolved or formally handed to an owner.",
    "Every open task and request is finished, transferred, or parked with the customer's agreement.",
    "The customer has agreed what happens next and received a short closeout recap.",
]

GOLDEN_RULES = [
    ("Blank beats invented", "Leave unknown values empty and create a follow-up. Never fill a number with a guess."),
    ("Evidence before Done", "A task is Done when its definition of done is met and checked, not when it looks finished."),
    ("People own the customer", "Agents draft, fill fields or flag. Every customer message and commitment is human."),
    ("Day 0 is payment", "Start date is the day the deal reached Start Payment Received. Kickoff is Days 5–10."),
    ("One row per engagement", "Every task, request and update links to its Customers row. A later onboarding gets a new row."),
    ("No silent scope", "New work goes through a request, a price and an approval."),
]

DATA_RULES = [
    ("Tasks created for", "Lists the products whose tasks exist. It says nothing about whether they're finished."),
    ("Customer Task: Done", "The definition of done is met and the evidence is recorded."),
    ("Request: Done", "The result is verified and communicated to the customer."),
    ("Current section: Completed", "The graduation gate is met and support has an owner. It is not a Health value."),
    ("Update: Draft / Reviewed / Sent", "An agent wrote it / the Architect checked it / it went to the customer. Only weekly updates and KPI snapshots can be Sent."),
    ("Current section and Next due task", "Portfolio summaries. The task rows are the truth."),
    ("Price", "USD, default 250. The default is not a quote and not the customer's approval."),
]

AUTOMATION = [
    ("Task Generator", "Copies the Core library plus one library per product into Customer Task, fills the dates and assigns the Architect's tasks.", "When Ops ticks Create tasks", "Ops checks the task count."),
    ("Handoff Brief", "Writes a one-page brief from the deal for the Architect and Phil.", "When a customer's tasks are first created", "Phil and the Architect review it before the handoff call."),
    ("Weekly Update Drafter", "Drafts each customer's Friday update.", "Thursdays, 9:00 AM Bogotá", "The Architect checks it, adds numbers, sends it and marks it Sent."),
    ("Delay Flagger", "Flags overdue and stuck tasks; sets Health to At risk at 3 or more overdue; alerts Phil when Health drops.", "Weekdays, 8:00 AM Bogotá", "The Architect confirms the impact and owns the recovery plan."),
    ("Request Triage", "Suggests the urgency, price and due date for each new request, and fills its Owner.", "When a request is logged", "The Architect confirms it with the customer."),
    ("Portfolio Sync", "Keeps each customer's Current section and Next due task up to date.", "Daily, 6:00 AM Bogotá", "If a summary looks wrong, fix the task data, not the summary."),
    ("What's Next Prep", "Drafts Option A and Option B for the next phase.", "35 days before the Target end date", "Phil and the Architect review it before the call."),
    ("KPI Snapshot Drafter", "Drafts the monthly KPI notes during free monitoring.", "1st of the month, 9:00 AM Bogotá", "The Architect adds the numbers and sends it."),
    ("Data rules", "Re-dates a customer's tasks when Start date or Program length changes, and only lets weekly updates and KPI snapshots be marked Sent.", "On every change", "Nothing to do."),
]

# ---------------------------------------------------------------- html parts
def step_html(s):
    who = "".join(f'<span class="who">{E(w)}</span>' for w in s["who"])
    return f"""<section class="step">
  <div class="step-head"><span class="num">{s['n']:02d}</span><div><h3>{E(s['title'])}</h3>
  <div class="meta"><span class="when">{E(s['when'])}</span>{who}</div></div></div>
  <ul class="check">{''.join(f"<li>{E(i)}</li>" for i in s['do'])}</ul>
  <p class="done"><b>Done when</b> {E(s['done'])}</p>
</section>"""


def table(headers, rows, cls=""):
    head = "".join(f"<th>{E(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def timeline():
    lo, hi = -30, 120
    pct = lambda v: (max(lo, min(hi, v)) - lo) / (hi - lo) * 100
    rows = []
    for p in d.PHASES:
        cls = "pre" if p["id"] == "P0" else "post" if p["id"] == "P9" else ""
        left, width = pct(p["start"]), max(1.2, pct(p["end"]) - pct(p["start"]))
        rows.append(f'<div class="tl-row"><div class="tl-label"><b>{p["id"]}</b> {E(p["name"])}</div>'
                    f'<div class="tl-track"><div class="tl-bar {cls}" style="left:{left:.2f}%;width:{width:.2f}%"></div></div>'
                    f'<div class="tl-days">{E(days(p["start"], p["end"]) if p["id"] != "P9" else "Day 90–270")}</div></div>')
    ticks = "".join(f'<span style="left:{pct(t):.2f}%">{"Day " + str(t) if t < 120 else "120+"}</span>' for t in (-30, 0, 30, 60, 90, 120))
    return f'<div class="timeline"><div class="tl-axis"><div></div><div class="tl-ticks">{ticks}</div><div></div></div>{"".join(rows)}</div>'


phase_order = [p["id"] for p in d.PHASES]
module_order = list(d.MODULES)
ordered = sorted(d.TASKS, key=lambda t: (phase_order.index(t[1]), module_order.index(d.module_of(t[0])), t[0]))
subtasks = defaultdict(list)
for area, item, det, tier, tid, owner in d.TECH_SETUP:
    subtasks[tid].append(item + (" (Ent)" if tier == "Ent only" else ""))


def library_html():
    out = []
    for pid in phase_order:
        ts = [t for t in ordered if t[1] == pid]
        p = PHASE[pid]
        rows = []
        for t in ts:
            tid, ph, task, det, owner, cf, s, e, dep, where, rep = t
            m = d.module_of(tid)
            extra = f'<div class="sub">Subtasks: {E("; ".join(subtasks[tid]))}</div>' if subtasks.get(tid) else ""
            rows.append([f'<span class="mono">{E(tid)}</span>',
                         f'<b>{E(task)}</b><div class="sub">{E(det)}</div>{extra}',
                         f'<span class="mod mod-{m}">{MODULE_LABEL[m]}</span>',
                         E(owner),
                         f'<span class="mono">{E("Before Day 0" if ph == "P0" else days(s, e))}</span>' + (f'<div class="sub">{E(rep)}</div>' if rep else ""),
                         "Yes" if cf == "Yes" else ""])
        out.append(f'<h3 class="lib-h">{pid} · {E(p["name"])} <span>{E(days(p["start"], p["end"]) if pid != "P9" else "Day 90–270")}</span></h3>'
                   + table(["ID", "Task and definition of done", "Module", "Owner", "When", "Client"], rows, "lib"))
    return "\n".join(out)


css = """
@page { size: Letter; margin: 0.7in 0.7in 0.75in 0.7in; }
@page :first { margin: 0; }
:root { --navy:#1f3a5f; --teal:#2e7d7a; --teal-soft:#dcefea; --ink:#17222e; --muted:#5b6876; --line:#d9e1e8; --chip:#eef3f7; --amber:#a85a0c; --amber-soft:#fbeedd; --violet:#6a4bb5; }
* { box-sizing: border-box; }
body { margin:0; font-family:"Inter", "Liberation Sans", sans-serif; font-size:9.6pt; line-height:1.5; color:var(--ink); -webkit-print-color-adjust:exact; print-color-adjust:exact; }
h1,h2,h3 { font-family:"Inter Display","Inter",sans-serif; color:var(--navy); margin:0; line-height:1.2; }
h2 { font-size:19pt; font-weight:700; margin:0 0 4pt; }
h3 { font-size:12pt; font-weight:600; }
p { margin:0 0 6pt; }
ul { margin:4pt 0 6pt; padding-left:14pt; }
li { margin:0 0 3pt; }
.mono { font-family:"JetBrains Mono", monospace; font-size:8.4pt; }
.eyebrow { font-family:"JetBrains Mono", monospace; font-size:7.6pt; letter-spacing:.12em; text-transform:uppercase; color:var(--teal); margin-bottom:4pt; }
.lede { font-size:10.5pt; color:var(--muted); max-width:6.2in; margin-bottom:12pt; }
.chapter { break-before:page; }
.keep { break-inside:avoid; }

/* cover */
.cover { height:11in; width:8.5in; display:flex; flex-direction:column; justify-content:space-between; padding:0.9in 0.85in; background:var(--navy); color:#fff; }
.cover .brand { font-family:"JetBrains Mono",monospace; font-size:9pt; letter-spacing:.18em; text-transform:uppercase; color:#9fd3cf; }
.cover h1 { color:#fff; font-size:38pt; font-weight:700; letter-spacing:-.01em; margin-top:1.6in; }
.cover .sub { font-size:14pt; color:#c9d6e3; margin-top:10pt; max-width:5.6in; line-height:1.4; }
.cover .hubs { display:flex; gap:8pt; margin-top:22pt; }
.cover .hubs span { border:1px solid #6f8fb3; border-radius:999px; padding:4pt 12pt; font-size:9.5pt; color:#e4ecf4; }
.cover .foot { display:grid; grid-template-columns:repeat(3,1fr); gap:12pt; border-top:1px solid #4a6a8f; padding-top:14pt; font-size:9pt; color:#c9d6e3; }
.cover .foot b { display:block; color:#fff; font-weight:600; margin-bottom:2pt; }
.cover .bars { display:grid; gap:5pt; margin-top:28pt; max-width:5.4in; }
.cover .bars i { display:block; height:7pt; border-radius:4pt; background:#2e7d7a; }

/* contents */
.toc { columns:2; column-gap:28pt; margin-top:10pt; }
.toc div { display:flex; gap:8pt; padding:5pt 0; border-bottom:1px solid var(--line); break-inside:avoid; font-size:10pt; }
.toc span { font-family:"JetBrains Mono",monospace; color:var(--teal); width:22pt; }

/* cards & grids */
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:8pt; }
.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:8pt; }
.card { border:1px solid var(--line); border-radius:6pt; padding:9pt 10pt; break-inside:avoid; }
.card h4 { margin:0 0 3pt; font-size:10pt; color:var(--navy); font-family:"Inter Display","Inter",sans-serif; }
.card p { margin:0; color:var(--muted); font-size:9pt; }
.stat { border-left:3px solid var(--teal); padding:2pt 0 2pt 9pt; }
.stat b { display:block; font-family:"Inter Display","Inter",sans-serif; font-size:18pt; color:var(--navy); line-height:1.1; }
.stat span { font-size:8.6pt; color:var(--muted); }

/* timeline */
.timeline { border:1px solid var(--line); border-radius:6pt; padding:10pt 12pt; margin:8pt 0 12pt; break-inside:avoid; }
.tl-row, .tl-axis { display:grid; grid-template-columns:1.75in 1fr 0.8in; align-items:center; gap:8pt; }
.tl-row { height:17pt; }
.tl-label { font-size:8.6pt; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.tl-label b { font-family:"JetBrains Mono",monospace; color:var(--teal); font-weight:500; margin-right:3pt; }
.tl-track { position:relative; height:9pt; background:linear-gradient(90deg, var(--chip) 1px, transparent 1px) 0 0/20% 100%; }
.tl-bar { position:absolute; top:0; height:9pt; border-radius:3pt; background:var(--teal); }
.tl-bar.pre { background:#9aa7b4; }
.tl-bar.post { background:repeating-linear-gradient(45deg, var(--teal), var(--teal) 4pt, var(--teal-soft) 4pt, var(--teal-soft) 8pt); }
.tl-days { font-family:"JetBrains Mono",monospace; font-size:7.6pt; color:var(--muted); text-align:right; }
.tl-ticks { position:relative; height:12pt; }
.tl-ticks span { position:absolute; transform:translateX(-50%); font-family:"JetBrains Mono",monospace; font-size:7pt; color:var(--muted); white-space:nowrap; }

/* steps */
.step { border:1px solid var(--line); border-radius:6pt; padding:10pt 12pt 8pt; margin:0 0 9pt; break-inside:avoid; }
.step-head { display:grid; grid-template-columns:30pt 1fr; gap:6pt; align-items:start; margin-bottom:2pt; }
.num { font-family:"JetBrains Mono",monospace; font-size:14pt; color:var(--teal); font-weight:500; }
.meta { display:flex; flex-wrap:wrap; gap:5pt; margin-top:3pt; align-items:center; }
.when { font-family:"JetBrains Mono",monospace; font-size:7.8pt; color:var(--muted); margin-right:4pt; }
.who { font-size:7.6pt; font-weight:600; padding:1pt 7pt; border-radius:999px; background:var(--chip); color:var(--navy); }
.step ul { margin-left:36pt; padding-left:14pt; }
.done { margin:5pt 0 0 36pt; padding:5pt 8pt; border-radius:4pt; background:var(--teal-soft); font-size:9pt; }
.done b { color:var(--teal); margin-right:4pt; }

/* tables */
table { width:100%; border-collapse:collapse; font-size:8.6pt; margin:6pt 0 12pt; }
thead { display:table-header-group; }
tr { break-inside:avoid; }
th { text-align:left; font-size:7.4pt; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-weight:600; padding:5pt 6pt; border-bottom:1.5px solid var(--navy); }
td { padding:5pt 6pt; border-bottom:1px solid var(--line); vertical-align:top; }
td .sub { color:var(--muted); font-size:8pt; margin-top:1pt; }
.lib td:nth-child(1) { width:0.68in; white-space:nowrap; } .lib td:nth-child(3) { width:0.7in; } .lib td:nth-child(4) { width:0.75in; } .lib td:nth-child(5) { width:0.85in; } .lib td:nth-child(6) { width:0.4in; }
.lib-h { margin-top:12pt; font-size:11pt; break-after:avoid; }
.lib-h span { font-family:"JetBrains Mono",monospace; font-size:8pt; color:var(--muted); font-weight:400; margin-left:6pt; }
.mod { font-size:7.4pt; font-weight:600; padding:1pt 6pt; border-radius:999px; white-space:nowrap; }
.mod-Core { background:var(--chip); color:var(--navy); }
.mod-MH { background:var(--teal-soft); color:var(--teal); }
.mod-SH { background:var(--amber-soft); color:var(--amber); }
.mod-SV { background:#ece6f8; color:var(--violet); }
.callout { border-left:3px solid var(--amber); background:var(--amber-soft); padding:8pt 10pt; border-radius:0 6pt 6pt 0; margin:8pt 0 12pt; font-size:9.2pt; break-inside:avoid; }
.check li { list-style:none; position:relative; }
.check li::before { content:""; position:absolute; left:-13pt; top:3pt; width:8pt; height:8pt; border:1.2px solid var(--teal); border-radius:2pt; }
ol.flow { padding-left:16pt; }
"""

toc_items = ["How to use this guide", "The program at a glance", "Roles and decision rights", "Where everything lives",
             "The procedure, step by step", "Requests", "Statuses and data rules", "The operating rhythm",
             "Automation you'll work with", "When things don't go to plan", "After the program",
             "A · Task library", "B · Progress measures", "C · Training modules", "D · Intake questions", "E · Technical setup checklist"]


roles_rows = [[f"<b>{E(r)}</b>", E(t)] for r, t in d.ROLES.items()] + [
    ["<b>Supporters & decision maker</b>", "Customer people confirmed from contact labels or explicit conversations. If unclear, the role stays an open question for the handoff or kickoff."]]
where_rows = [[f"<b>{E(t)}</b>", E(j)] for t, j in d.WHERE_IT_LIVES if not t.startswith("Not used")]
customers_rows = [[f"<b>{E(c)}</b>", E(t)] for c, t in d.WORK_PORTFOLIO_COLUMNS]
taskcol_rows = [[f"<b>{E(c)}</b>", E(t), E(n)] for c, t, n in d.WORK_TASK_COLUMNS]

HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>RevGravy Customer Onboarding SOP</title><style>{css}</style></head><body>

<div class="cover">
  <div>
    <div class="brand">RevGravy · Standard operating procedure</div>
    <h1>Customer Onboarding</h1>
    <div class="sub">How a customer goes from signed deal to graduation and six months beyond, and who does what at every step.</div>
    <div class="hubs"><span>Marketing Hub</span><span>Sales Hub</span><span>Service Hub</span><span>60–90 days</span></div>
    <div class="bars">{''.join(f'<i style="width:{w}%;margin-left:{m}%;opacity:{o}"></i>' for w, m, o in [(20,0,.45),(3,20,1),(6,21,1),(5,23,1),(15,25,1),(36,34,1),(47,29,.8),(55,25,.6),(20,60,1),(20,80,.5)])}</div>
  </div>
  <div class="foot">
    <div><b>Version</b>1.0 · {VERSION_DATE}</div>
    <div><b>Runs in</b>HubSpot Work · Supered · HubSpot CRM</div>
    <div><b>Owner</b>RevGravy Operations</div>
  </div>
</div>

<section class="chapter">
  <div class="eyebrow">Contents</div>
  <h2>What's inside</h2>
  <div class="toc">{''.join(f'<div><span>{i+1:02d}</span>{E(t)}</div>' if not t[1:3] == " ·" else f'<div><span>{t[0]}</span>{E(t[4:])}</div>' for i, t in enumerate(toc_items))}</div>

  <div style="margin-top:22pt" class="eyebrow">01 · How to use this guide</div>
  <h2>Read it once, then work from the steps</h2>
  <p class="lede">Chapter 05 is the procedure: thirteen steps, each with a checklist and the condition that closes it. Everything else supports it. The appendices list every task, measure, training module, intake question and setup item, so you can see what a hub includes without opening HubSpot Work.</p>
  <div class="grid3">{''.join(f'<div class="card"><h4>{E(h)}</h4><p>{E(t)}</p></div>' for h, t in GOLDEN_RULES)}</div>
</section>

<section class="chapter">
  <div class="eyebrow">02 · The program at a glance</div>
  <h2>Ten phases, one customer, 60 to 90 days</h2>
  <p class="lede">Day 0 is the day payment lands. Week one is the same for every program; later dates compress for 60- and 75-day programs. Phases overlap on purpose: they are planning windows, not gates.</p>
  <div class="grid3" style="margin-bottom:6pt">
    <div class="stat"><b>{len(d.TASKS)}</b><span>tasks in the library</span></div>
    <div class="stat"><b>{count['Core']} + 1 module</b><span>Core tasks once, plus one module per hub</span></div>
    <div class="stat"><b>{len(d.WORK_AGENTS)}</b><span>agents that draft, fill or flag</span></div>
  </div>
  {timeline()}
  {table(["Phase", "Goal", "What the customer sees", "Done when"],
         [[f'<b>{p["id"]}</b><div class="sub">{E(p["name"])}</div>', E(p["goal"].replace(" No Trello.", "")), E(p["client_sees"]), E(p["exit"])] for p in d.PHASES])}
</section>

<section class="chapter">
  <div class="eyebrow">03 · Roles and decision rights</div>
  <h2>Who does what</h2>
  <p class="lede">Phil leads through the sale and the handoff. After the handoff call the Architect is the strategy lead, including the what's next call. Owner role says who acts; Assignee is always a real internal person, even when the customer has the action.</p>
  {table(["Role", "Responsibility"], roles_rows)}

  <div class="eyebrow" style="margin-top:16pt">04 · Where everything lives</div>
  <h2>HubSpot Work runs it, Supered shows it</h2>
  <p class="lede">CRM is the source for companies, deals, contacts, quotes and products. HubSpot Work is the source for the engagement, its tasks, requests, health, measures and drafts. Supered is everything the customer sees.</p>
  {table(["Tool", "Its job"], where_rows)}
  <div class="grid2 keep">
    <div class="card"><h4>Onboarding Task Library project</h4><p>Four library tables: Onboarding Library (Core, {count['Core']} tasks), Marketing Onboarding Library ({count['MH']}), Sales Onboarding Library ({count['SH']}), Service Onboarding Library ({count['SV']}). Templates only; nobody works in them.</p></div>
    <div class="card"><h4>Onboarding Portfolio project</h4><p>Customers (one row per engagement), Customer Task (every customer's tasks), Request (every request), Update (drafts for the Architect). Every row links to its Customers row.</p></div>
  </div>
  <h3 style="margin-top:14pt">Customers table</h3>
  {table(["Column", "What goes in it"], customers_rows)}
</section>

<section class="chapter">
  <div class="eyebrow">05 · The procedure</div>
  <h2>Step by step, from sale to six months after</h2>
  <p class="lede">Each step names when it happens, who acts, what they do, and the condition that closes it. Task IDs refer to Appendix A.</p>
  {''.join(step_html(s) for s in d and STEPS)}
  <div class="card keep" style="margin-top:4pt"><h4>Graduation gate</h4><ul class="check">{''.join(f'<li>{E(g)}</li>' for g in GRADUATION_GATE)}</ul><p>Only then set Current section to Completed. Keep the row as history; a later onboarding gets a new row.</p></div>
</section>

<section class="chapter">
  <div class="eyebrow">06 · Requests</div>
  <h2>$250 per request, handled by urgency</h2>
  <p class="lede">The Request table is internal. Customers ask by email, Slack, in office hours or in Supered, and the Architect logs it the same day.</p>
  {ul(d.REQUEST_RULES)}
  {table(["Urgency", "What it is", "Response and turnaround", "Price"], [[f"<b>{E(u)}</b>", E(w), E(t), E(p)] for u, w, t, p in d.REQUEST_CLASSES])}
  {table(["Status", "Meaning"], [["<b>New</b>", "Logged, not yet triaged. Confirm owner, urgency, type and next step."],
                                 ["<b>Quoted</b>", "Scope, price and date proposed. No chargeable work until the customer approves."],
                                 ["<b>In progress</b>", "Approved and started. Keep the owner, due date and next update current."],
                                 ["<b>Done</b>", "Verified and communicated, with customer validation where needed."],
                                 ["<b>Parked</b>", "Deferred or declined, with the reason and a review date. Feeds the what's next call."]])}

  <div class="eyebrow" style="margin-top:14pt">07 · Statuses and data rules</div>
  <h2>When to change a status</h2>
  {table(["Task status", "When"], [[f"<b>{E(s)}</b>", E(t)] for s, t in d.STATUS_RULES])}
  {table(["Field or state", "What it means"], [[f"<b>{E(s)}</b>", E(t)] for s, t in DATA_RULES])}
</section>

<section class="chapter">
  <div class="eyebrow">08 · The operating rhythm</div>
  <h2>A normal week</h2>
  {table(["When", "Who", "What happens"], [[f'<span class="mono">{E(w)}</span>', f"<b>{E(who)}</b>", E(t)] for w, who, t in d.WEEKLY_RHYTHM])}
  <div class="grid3 keep">
    <div class="card"><h4>Every working day</h4><ul class="check"><li>Review due and overdue tasks; separate delays from Waiting on client.</li><li>Every blocked item has an owner and a next action.</li><li>Triage new requests.</li><li>Review Health changes and delay flags.</li></ul></div>
    <div class="card"><h4>Every week</h4><ul class="check"><li>Send the Friday update and mark it Sent.</li><li>Set Health from evidence.</li><li>Check Current section and Next due task.</li><li>Phil's delivery review.</li></ul></div>
    <div class="card"><h4>Every month</h4><ul class="check"><li>MBR: actuals vs baseline and target.</li><li>Reconfirm scope, risks and measure owners.</li><li>Near the end: prepare the what's next options.</li></ul></div>
  </div>
  <h3 style="margin-top:14pt">Customer touchpoints</h3>
  {table(["Touchpoint", "Timing", "Channel", "Owner", "Content"], [[f"<b>{E(a)}</b>", E(b), E(c), E(o), E(t)] for a, b, c, o, t in d.COMMS])}
</section>

<section class="chapter">
  <div class="eyebrow">09 · Automation you'll work with</div>
  <h2>What HubSpot Work does for you, and what you still own</h2>
  <p class="lede">Agents only draft, fill fields or flag. None of them sends anything to a customer or changes a deal. Every draft waits for a person.</p>
  {table(["Automation", "What it does", "When it runs", "What you do"],
         [[f"<b>{E(n)}</b>", E(w), E(t), E(g)] for n, w, t, g in AUTOMATION])}

  <div class="eyebrow" style="margin-top:14pt">10 · When things don't go to plan</div>
  <h2>Exceptions</h2>
  {table(["Situation", "What to do"], [[f"<b>{E(s)}</b>", E(t.split(" In the example")[0])] for s, t in d.EXCEPTIONS] + [
      ["<b>Agreement or approval is missing</b>", "Keep the engagement out of active delivery until a start is authorized. Record the gap, an owner and the next action."],
      ["<b>A draft contains a wrong or unsupported claim</b>", "Don't share it. Fix the source record, revise the draft, and have the Architect confirm the evidence."],
      ["<b>The program ends with open items</b>", "Agree item by item: finish, hand to support, or park. Don't set Completed until each has an owner."]])}
</section>

<section class="chapter">
  <div class="eyebrow">11 · After the program</div>
  <h2>6 months free, then a paid next step</h2>
  <p class="lede">Monitoring starts the day the program ends. The Architect runs every check-in and presents the paid options at month 5.</p>
  {table(["Offer", "Price", "What's included"], [[f"<b>{E(o)}</b>", E(p.replace(" (existing 'Monthly Plan – Standard', 1 task at a time)", " (Monthly Plan – Standard, one task at a time)").replace("To be priced", "Quoted per customer")), E(w)] for o, p, w in d.POST_PROGRAM])}
  {table(["When", "What happens"], [["<b>Monthly</b>", "KPI snapshot email: the progress-measure dashboard with 3 short notes from the Architect."],
                                     ["<b>Any time</b>", "Portal health alerts: deliverability drops, workflow errors, form submissions falling. Tell the customer when one fires."],
                                     ["<b>Month 3</b>", "30-minute check-in: numbers, what's working, what's next."],
                                     ["<b>Month 5</b>", "Paid offer conversation: team support, building internal capacity, or one initiative a month."],
                                     ["<b>Month 6</b>", "Last check-in. A paid offer becomes a new deal; otherwise set Current section to Completed."]])}
</section>

<section class="chapter">
  <div class="eyebrow">Appendix A</div>
  <h2>Task library</h2>
  <p class="lede">Every customer gets the Core tasks once, plus the module for each hub bought. Days are for a 90-day program. Module colors: <span class="mod mod-Core">Core</span> <span class="mod mod-MH">Marketing</span> <span class="mod mod-SH">Sales</span> <span class="mod mod-SV">Service</span></p>
  {library_html()}
</section>

<section class="chapter">
  <div class="eyebrow">Appendix B</div>
  <h2>Progress measures</h2>
  <p class="lede">Name each one after the customer, e.g. "&lt;Client&gt; 1.1 Visitor to Lead". 1.x is Marketing, 2.x and 3.x are Sales, 4.x is Service. "Every" measures go into every program for that hub; the others only when bought.</p>
  {table(["ID", "Progress measure", "When", "What it measures", "HubSpot report", "Built by"], [[f'<span class="mono">{E(i)}</span>', f"<b>{E(n)}</b>", E(w), E(m), E(r), f'<span class="mono">{E(b)}</span>'] for i, n, w, m, r, b in d.FACTORIES])}

  <div class="eyebrow" style="margin-top:14pt">Appendix C</div>
  <h2>Training modules</h2>
  {table(["Module", "Audience", "Content", "Format", "When", "Length"], [[f"<b>{E(a)}</b>", E(b), E(c), E(f), E(w), E(l)] for a, b, c, f, w, l in d.TRAINING])}
</section>

<section class="chapter">
  <div class="eyebrow">Appendix D</div>
  <h2>Intake questions</h2>
  <p class="lede">Only what pre-sale didn't capture. Items marked as pre-filled are shown to the customer to confirm.</p>
  {table(["Section", "Question", "Field", "Required", "Pre-filled?", "Why we ask"], [[f"<b>{E(s)}</b>", E(q), E(f), E(r), E(p), E(w)] for s, q, f, r, p, w, m in d.INTAKE])}
</section>

<section class="chapter">
  <div class="eyebrow">Appendix E</div>
  <h2>Technical setup checklist</h2>
  <p class="lede">Each item is a subtask of the task in the last column. "Ent only" items apply to Enterprise customers.</p>
  {table(["Area", "Item", "Details", "Tier", "Task"], [[f"<b>{E(a)}</b>", E(i), E(det), E(t), f'<span class="mono">{E(tid)}</span>'] for a, i, det, t, tid, o in d.TECH_SETUP])}
</section>

</body></html>"""

if __name__ == "__main__":
    OUT_HTML.write_text(HTML, encoding="utf-8")
    print(f"Saved {OUT_HTML}")
