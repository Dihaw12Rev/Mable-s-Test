"""Build RevGravy_New_Client_Start_SOP.pdf (and start.html): how to start the client whose Day 0 is 5 Nov 2026,
including how to run the 1:1 that launches it.

Run:  python3 build_start_pdf.py && node render_pdf.js start.html RevGravy_New_Client_Start_SOP.pdf "RevGravy · New Client Start SOP"
"""
from datetime import date, timedelta
from pathlib import Path

import build_sop_pdf as base
import process_data as d

HERE = Path(__file__).parent
E = base.E
table = base.table
DAY0 = date(2026, 11, 5)
TASK = {t[0]: t[2] for t in d.TASKS}
CORE_PLUS_MH = sum(1 for t in d.TASKS if d.module_of(t[0]) in ("Core", "MH"))


def on(n, weekday=True):
    dt = DAY0 + timedelta(days=n)
    return (f"{dt:%a} " if weekday else "") + f"{dt:%b} {dt.day}"


def checklist(items):
    return '<ul class="check">' + "".join(
        f"<li><b>{E(h)}</b>{'<div class=sub>' + E(t) + '</div>' if t else ''}</li>" for h, t in items) + "</ul>"


def done_ids(ids):
    return '<div class="marks"><span>Mark Done in HubSpot Work</span>' + "".join(
        f'<em><b>{E(i)}</b> {E(TASK[i])}</em>' for i in ids) + "</div>"


# ------------------------------------------------------------------ content
OUTCOMES_MEETING = [
    ("The client is live in HubSpot Work", f"The Customers row is complete, Create tasks has run, and {CORE_PLUS_MH} tasks show with the right dates."),
    ("The launch scope is agreed", "What we use from day one, what we do by hand for this client, and what waits."),
    ("The call rhythm is set", "Weekly jam day and time, the kickoff jam window, and MBR dates."),
    ("Supered has a job list", "Who posts the welcome, the weekly update and delivery videos, and who owns the config templates."),
    ("Agents are on", "The ones that help from day one are switched on."),
    ("Progress measures are written", "Names, where the baseline comes from, and a target, even if the numbers come later."),
    ("Every open item has an owner and a date", "Nothing leaves the meeting as \"we'll figure it out\"."),
]

OUTCOMES_WEEK2 = [
    ("Access and intake are in", "By Day 7 (" + on(7) + ")."),
    ("The kickoff jam has happened", "Between Day 5 and Day 10 (" + on(5) + " – " + on(10) + ")."),
    ("The first weekly update is posted", "In Supered on " + on(8) + "."),
    ("The first weekly jam has happened", "In the week of " + on(11, False) + "."),
    ("Health is On track", "With no P1–P3 task overdue."),
]

PILOT_MEASURES = [
    ("Access and intake complete", "By Day 7", "Customer Task 2.01–2.04 Done"),
    ("Kickoff jam held", "By Day 10", "Task 3.02 Done"),
    ("Jam action items logged", "Within 24 hours, every time", "New tasks or requests dated the jam day"),
    ("Friday update posted", "Every week", "Update rows marked Sent"),
    ("Overdue tasks flagged", "None overdue more than 3 days without a flag", "Overdue view + Delay Flagger"),
    ("Architect admin time", "Noted each week", "The Architect's own estimate"),
]

PREP = [
    ("Paste the fix-up prompt", "HubSpot Work › Client Onboarding › chat. Paste hubspot-work-fix-prompt.txt and approve the plan.",
     ["Onboarding Library shows 58 tasks.", "Customers has Products purchased, Create tasks and Tasks created for.", "Agent schedules show Bogotá time."]),
    ("Build the missing agents", "HubSpot Work › Agents › New agent. For each, start from the named sample or a blank agent and paste its prompt from hubspot-work-agent-prompts.md.",
     ["Onboarding Task Generator (sample: Auto-create customer onboarding).", "Weekly Update Drafter (sample: Weekly stakeholder updates).", "Request Triage (sample: Auto-route requests)."]),
    ("Fill the client's Customers row", "Onboarding Portfolio › Customers › the row starting Nov 5.",
     ["Products purchased = Marketing Hub Onboarding.", "Program length = 90, Start date = Nov 5, Hub tiers = Marketing Pro.", "Architect, Company and Deal filled.", "Progress measures: 0.1, 1.1, 1.2, 1.3, with baseline 'to measure in the audit' and a target if Phil has one.", "Leave Create tasks unticked. You'll tick it in the meeting."]),
    ("Share the workspace", "Share on the Client Onboarding workspace.",
     ["Phil and the Architect can open both projects."]),
    ("Set up the jam board", "Duplicate the sales FigJam for this client.",
     ["Sections: Goal, Progress measures, This week, Decisions, Not now.", "Link saved in the Customers row's FigJam link."]),
    ("Draft the welcome pieces", "Use the drafts in Appendix A.",
     ["Welcome email, ready to send.", "\"How we work\" Supered announcement, ready to post."]),
]

MEETING = [
    {"t": "0–5", "title": "Put the client live", "goal": "See the tasks appear.",
     "do": ["Open Onboarding Portfolio › Customers and show the client's row.", "Tick Create tasks.", "Open Customer Task › By customer and filter to the client."],
     "check": [f"{CORE_PLUS_MH} tasks appear (Core + Marketing Hub).", f"4.11 is due {on(30, False)}, 8.05 is due {on(90, False)}, 2027; P0 tasks have no date.", "Tasks created for = Marketing Hub Onboarding; Create tasks unticked itself."],
     "if": "If no tasks appear within 15 minutes, move on. Ops copies them by hand after the meeting."},
    {"t": "5–15", "title": "Agree the launch scope", "goal": "Everyone knows what's real for this client.",
     "do": ["Walk the three lists: use from day one, by hand for this client, after this client.", "Move anything that's in the wrong list."],
     "check": ["Decision log rows 1–2 filled."],
     "if": "If something is in neither list, it waits until after this client."},
    {"t": "15–25", "title": "Set the jam rhythm", "goal": "The calendar for the next 90 days is decided.",
     "do": ["Pick the weekly jam day, time and length. Suggested: Thursday, 30 minutes, so the Friday update can summarize it.",
            "Confirm the kickoff jam is 30 minutes, between " + on(5, False) + " and " + on(10, False) + ".",
            f"Confirm the MBR jams: {on(29)} (Day 30 is a Saturday) and {on(60)}.",
            "Agree the rule: every jam action item becomes a task or request in HubSpot Work the same day."],
     "check": ["Decision log rows 3–5 filled."],
     "if": "If the day can't be fixed yet, the Architect proposes it to the client in the welcome email."},
    {"t": "25–35", "title": "Supered: announcements and templates", "goal": "Supered has clear jobs and an owner.",
     "do": ["Agree what Supered carries: the Action Plan, the welcome announcement, the Friday update, delivery videos.",
            "Ask which HubSpot config templates Supered holds today.",
            "Pick the first three templates to map to library tasks (candidates: 4.05 lifecycle stages, 4.10 baseline dashboard, MH-5.02 lead scoring and nurture)."],
     "check": ["Decision log rows 6–7 filled.", "Template owner named."],
     "if": "If no templates exist yet, build in the portal as usual and note which builds should become templates."},
    {"t": "35–40", "title": "Switch the agents on", "goal": "The automation that helps from day one is running.",
     "do": ["Resume: Task Generator, Handoff Brief, Delay Flagger, Portfolio Sync, Request Triage, Weekly Update Drafter.",
            "Leave What's Next Prep and KPI Snapshot as they are; they don't fire until January and February."],
     "check": ["Decision log row 8 filled."],
     "if": "If one misbehaves later, pause just that one and keep going by hand."},
    {"t": "40–45", "title": "Close out this client's handoff", "goal": "The Architect can start tomorrow without questions.",
     "do": ["Confirm the progress measures and where each baseline will come from.", "List any missing pre-sale items and who fixes them.", "Confirm who sends the welcome (suggested: the Architect, today)."],
     "check": ["Decision log rows 9–10 filled.", "Every row has an owner and a date."],
     "if": "If a measure can't be agreed, leave it blank with an owner. Decide it at the handoff jam."},
]

DECISIONS = [
    "Launch scope: anything moved between the three lists",
    "Welcome email: who sends it, and when",
    "Weekly jam: day, time, length",
    "Kickoff jam: length and date window",
    "Office hours: replaced by the weekly jam, yes or no",
    "Weekly update: Supered announcement, yes or no",
    "Supered config templates: owner and first three",
    "Agents switched on",
    "Progress measures: names, baseline source, target",
    "Missing pre-sale items: owner and fix date",
]

AFTER = [
    ("Send the welcome email", "From the Architect, using Appendix A. Mark 1.03 Done.", ["1.03"]),
    ("Post the \"How we work\" announcement", "In Supered, using Appendix A. It replaces welcome email #2 for this client.", ["1.08"]),
    ("Build the Supered Action Plan", "Two to-dos for the client this week: grant HubSpot access, and answer the intake questions. Add the kickoff booking link.", ["1.04"]),
    ("Book the handoff jam", "Phil and the Architect, 30 minutes, before " + on(3) + " (use Monday " + on(4, False) + " because Day 3 is a Sunday).", []),
    ("Close the Day 0 tasks", "Architect picked, customer added in HubSpot Work.", ["1.01", "1.02"]),
    ("Send me the decision log", "So the SOP, the library and the agent prompts get updated to match.", []),
]

TEN_DAYS = [
    (0, 0, "Day 0", "1:1. Client goes live. Welcome email and announcement out.", ["1.01", "1.02", "1.03", "1.04"]),
    (1, 4, "Days 1–4", "Handoff jam (Phil + Architect): walk P0, record progress measures, mark P0 Done or send gaps back to Phil. Client works on access and intake. Chase on Monday " + on(4, False) + ".", ["1.05", "1.06", "1.07", "1.09"]),
    (3, 7, "Days 3–7", "Portal audit and baseline numbers as soon as access works.", ["2.01", "2.02", "2.06", "2.07"]),
    (5, 8, "Days 5–8", "Kickoff jam (30 min). Book the weekly jam, MBR jams, what's next jam and final results jam. Send the recap within 24 hours.", ["3.01", "3.02", "3.03", "3.04"]),
    (8, 8, "Day 8", "First Friday update posted in Supered.", []),
    (11, 15, "Days 11–15", "First weekly jam. Foundations start (account, tracking, domains, email).", []),
]

KICKOFF_AGENDA = [
    ("0–5", "Introductions: the Architect, the team, the client's people and who decides what."),
    ("5–15", "On the board: the From→To goal, the progress measures and the 90-day plan."),
    ("15–25", "Missing items: access, intake answers, brand files. Each gets an owner and a date."),
    ("25–30", "How we work: Thursday jams, Friday updates in Supered, MBRs, how to send a request."),
]

WELCOME_EMAIL = """Subject: Welcome to RevGravy: here's how we start

Hi {first name},

Welcome aboard. I'm {Architect}, your Architect for the next 90 days. I'll lead the work and I'm your main contact.

This week:
1. Your Action Plan is live in Supered: {Supered link}. It has two things for you: give us access to HubSpot, and answer a few intake questions. Together they take about 15 minutes.
2. Book our kickoff: a 30-minute working session on a shared board. Any slot from Tue Nov 10 to Fri Nov 13: {booking link}.

After that, we meet every {Thursday} for 30 minutes, and you'll get a short update in Supered every Friday.

Our goal together: {From→To goal}.

If anything is urgent, reply to this email. I'll get back to you within one business day.

{Architect}
RevGravy"""

HOW_WE_WORK = """Title: How we'll work together

Where things live
- Supered: your Action Plan, our updates and short videos of what we build.
- Our shared board: every call is a working session on the same board, so decisions stay in one place.
- Email: anything urgent.

Our rhythm
- Every {Thursday}: a 30-minute working session.
- Every Friday: a short update here with what we did and why it matters, your numbers against where we started, anything we found, next week's plan, and your to-dos.
- Monthly reviews: around Dec 4 and Jan 4.

Requests
- Small extra requests (about 2 hours of work) are $250 each. We confirm the price before we start.
- If something we built breaks, we fix it within one business day at no charge.
- We reply to every other request within one business day.

AI
- We use AI to draft some updates. A person reviews everything before it reaches you."""

WEEKLY_UPDATE = """Title: Week of {date}

1. What we did, and why it matters: {two or three lines tied to the goal}
2. Your numbers: {progress measures vs baseline}
3. What we found: {anything outside the plan worth knowing}
4. Next week: {two or three lines}
5. Your to-dos: {items, with dates}"""

# ------------------------------------------------------------------ html
css = base.css + """
.outcome { display:grid; grid-template-columns:1fr 1fr; gap:8pt; }
.outcome .card b { display:block; color:var(--navy); font-size:10pt; margin-bottom:2pt; }
.prep { border:1px solid var(--line); border-radius:6pt; padding:10pt 12pt; margin:0 0 8pt; break-inside:avoid; }
.prep h3 { font-size:11.5pt; }
.prep .where { font-size:8.8pt; color:var(--muted); margin:2pt 0 4pt; }
.prep ul.check { margin-left:14pt; }
.block { border:1px solid var(--line); border-radius:6pt; margin:0 0 9pt; break-inside:avoid; overflow:hidden; }
.block-head { display:grid; grid-template-columns:62pt 1fr; gap:8pt; padding:9pt 12pt 6pt; border-bottom:1px solid var(--line); background:var(--chip); }
.block-head .t { font-family:"JetBrains Mono",monospace; font-size:11pt; color:var(--teal); }
.block-head h3 { font-size:11.5pt; }
.block-head p { margin:1pt 0 0; font-size:9pt; color:var(--muted); }
.block-body { display:grid; grid-template-columns:1.25fr 1fr; gap:12pt; padding:8pt 12pt 10pt; }
.block-body h4 { margin:0 0 3pt; font-size:7.6pt; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-family:"JetBrains Mono",monospace; font-weight:500; }
.block-body ul { margin:0 0 6pt; }
.iff { grid-column:1 / -1; font-size:8.8pt; background:var(--amber-soft); border-radius:4pt; padding:5pt 8pt; }
.iff b { color:var(--amber); margin-right:4pt; }
.log td { height:26pt; }
.log td:first-child { width:18pt; font-family:"JetBrains Mono",monospace; color:var(--muted); }
.log td:nth-child(2) { width:2.1in; }
.marks { margin-top:4pt; display:flex; flex-wrap:wrap; gap:4pt; align-items:center; font-size:8pt; }
.marks span { color:var(--teal); font-weight:600; margin-right:2pt; }
.marks em { font-style:normal; background:var(--teal-soft); border-radius:4pt; padding:1pt 5pt; }
.marks em b { font-family:"JetBrains Mono",monospace; font-weight:500; color:var(--teal); }
.tl2 { border:1px solid var(--line); border-radius:6pt; }
.tl2 > div { display:grid; grid-template-columns:1.25in 1fr; gap:10pt; padding:8pt 12pt; border-bottom:1px solid var(--line); break-inside:avoid; }
.tl2 > div:last-child { border-bottom:0; }
.tl2 .d { font-family:"JetBrains Mono",monospace; font-size:8.6pt; }
.tl2 .d span { display:block; color:var(--muted); font-size:7.8pt; }
pre.tpl { white-space:pre-wrap; font-family:"Inter",sans-serif; font-size:9pt; line-height:1.5; border:1px solid var(--line); border-left:3px solid var(--teal); border-radius:0 6pt 6pt 0; padding:10pt 12pt; margin:4pt 0 12pt; break-inside:avoid; background:#fff; }
.goal-banner { border-radius:8pt; background:var(--navy); color:#fff; padding:14pt 16pt; margin:8pt 0 14pt; break-inside:avoid; }
.goal-banner .eyebrow { color:#9fd3cf; }
.goal-banner p { color:#fff; font-size:12.5pt; line-height:1.45; margin:0; font-family:"Inter Display","Inter",sans-serif; }
"""


def block_html(b):
    return f"""<div class="block">
  <div class="block-head"><span class="t">{E(b['t'])} min</span><div><h3>{E(b['title'])}</h3><p>{E(b['goal'])}</p></div></div>
  <div class="block-body">
    <div><h4>Do</h4>{base.ul(b['do'])}</div>
    <div><h4>Check before moving on</h4><ul class="check">{''.join(f'<li>{E(c)}</li>' for c in b['check'])}</ul></div>
    <div class="iff"><b>If it goes sideways</b>{E(b['if'])}</div>
  </div>
</div>"""


def prep_html(i, p):
    title, where, checks = p
    return f"""<div class="prep"><div class="step-head"><span class="num">{i:02d}</span><div><h3>{E(title)}</h3>
  <div class="where">{E(where)}</div><ul class="check">{''.join(f'<li>{E(c)}</li>' for c in checks)}</ul></div></div></div>"""


HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>RevGravy New Client Start SOP</title><style>{css}</style></head><body>

<div class="cover">
  <div>
    <div class="brand">RevGravy · Standard operating procedure</div>
    <h1>Starting a New Client</h1>
    <div class="sub">How to put a new Marketing Hub client live on HubSpot Work, jam sessions and Supered: the prep, the launch meeting, Day 0, and the first two weeks.</div>
    <div class="hubs"><span>Day 0 · {on(0)}, 2026</span><span>90 days</span><span>Marketing Hub Pro</span></div>
  </div>
  <div class="foot">
    <div><b>Version</b>1.0 · November 2026</div>
    <div><b>Companion to</b>Customer Onboarding SOP v1.0</div>
    <div><b>Owner</b>RevGravy Operations</div>
  </div>
</div>

<section class="chapter">
  <div class="eyebrow">01 · The goal</div>
  <h2>What good looks like</h2>
  <div class="goal-banner"><div class="eyebrow">By the end of the launch meeting</div>
    <p>The client is live in HubSpot Work, everyone knows the plan for the first ten days, and every open decision has an owner and a date.</p></div>
  <h3>The meeting is done when</h3>
  <div class="outcome" style="margin-top:6pt">{''.join(f'<div class="card"><b>{E(h)}</b><p>{E(t)}</p></div>' for h, t in OUTCOMES_MEETING)}</div>
  <h3 style="margin-top:14pt">Two weeks later, on {on(15)}</h3>
  <ul class="check">{''.join(f'<li><b>{E(h)}</b> {E(t)}</li>' for h, t in OUTCOMES_WEEK2)}</ul>
  <p class="muted" style="margin-top:8pt">Chapter 07 has the measures we'll use to judge the new way of working at the two-week check-in.</p>
</section>

<section class="chapter">
  <div class="eyebrow">02 · Before the meeting</div>
  <h2>Prep, in order</h2>
  <p class="lede">About an hour. Each step says where to go in HubSpot Work and what to check before moving on.</p>
  {''.join(prep_html(i, p) for i, p in enumerate(PREP, start=1))}
  <div class="callout"><b>Bring to the meeting:</b> the Customer Onboarding SOP, this guide with the decision log (chapter 04) printed or open, and HubSpot Work open on the client's Customers row.</div>
</section>

<section class="chapter">
  <div class="eyebrow">03 · Running the meeting</div>
  <h2>45 minutes, six blocks</h2>
  <p class="lede">Keep to the blocks. Each one has a goal, what to do on screen, what to check before moving on, and what to do if it goes sideways. Write every decision in the log as you go.</p>
  {''.join(block_html(b) for b in MEETING)}
</section>

<section class="chapter">
  <div class="eyebrow">04 · Decision log</div>
  <h2>Fill this in during the meeting</h2>
  <p class="lede">One row per decision. A row without an owner and a date isn't finished.</p>
  <table class="log"><thead><tr><th>#</th><th>Decision</th><th>What we chose</th><th>Owner</th><th>By when</th></tr></thead><tbody>
  {''.join(f'<tr><td>{i}</td><td>{E(t)}</td><td></td><td></td><td></td></tr>' for i, t in enumerate(DECISIONS, start=1))}
  {''.join(f'<tr><td>{i}</td><td></td><td></td><td></td><td></td></tr>' for i in range(len(DECISIONS) + 1, len(DECISIONS) + 4))}
  </tbody></table>
</section>

<section class="chapter">
  <div class="eyebrow">05 · Right after the meeting</div>
  <h2>Day 0, same day</h2>
  <p class="lede">In this order, before the end of {on(0)}.</p>
  {''.join(f'<div class="prep"><div class="step-head"><span class="num">{i:02d}</span><div><h3>{E(h)}</h3><div class="where">{E(t)}</div>{done_ids(ids) if ids else ""}</div></div></div>' for i, (h, t, ids) in enumerate(AFTER, start=1))}

  <div class="eyebrow" style="margin-top:16pt">06 · The first ten days</div>
  <h2>What happens, and what to mark Done</h2>
  <div class="tl2">{''.join(f'<div><span class="d">{E(on(a, False) if a == b else on(a, False) + " – " + on(b, False))}<span>{E(lbl)}</span></span><div>{E(txt)}{done_ids(ids) if ids else ""}</div></div>' for a, b, lbl, txt, ids in TEN_DAYS)}</div>
  <div class="callout" style="margin-top:12pt"><b>Dates to keep in mind.</b> Thanksgiving is Day 21 ({on(21)}); avoid asking for sign-offs that week. MBR #1 is {on(29)}, because Day 30 is a Saturday. Christmas is Day 50 and New Year's Day is Day 57, so plan the what's next jam for the week of {on(60, False)}.</div>

  <div class="eyebrow" style="margin-top:16pt">07 · Two-week check-in</div>
  <h2>{on(15)}, 15 minutes</h2>
  {table(["Measure", "Target", "Where to see it"], [[f"<b>{E(a)}</b>", E(b), E(c)] for a, b, c in PILOT_MEASURES])}
  <ul class="check"><li>Go through the measures above. Which were hit, which weren't, and why.</li>
  <li>Decide the next thing to automate. Suggested order: welcome email series, then the intake form, then Supered config templates.</li>
  <li>Decide whether the next client starts the same way, or with changes.</li></ul>
</section>

<section class="chapter">
  <div class="eyebrow">Appendix A</div>
  <h2>Ready-to-use drafts</h2>
  <p class="lede">Replace everything in {{curly brackets}}. Keep the tone plain and short.</p>
  <h3>Welcome email (from the Architect, Day 0)</h3>
  <pre class="tpl">{E(WELCOME_EMAIL)}</pre>
  <h3>"How we work" Supered announcement (Day 0)</h3>
  <pre class="tpl">{E(HOW_WE_WORK)}</pre>
  <h3>Kickoff jam agenda (30 minutes)</h3>
  {table(["Minutes", "On the board"], [[f'<span class="mono">{E(a)}</span>', E(b)] for a, b in KICKOFF_AGENDA])}
  <h3>Friday update (Supered announcement)</h3>
  <pre class="tpl">{E(WEEKLY_UPDATE)}</pre>
</section>

</body></html>"""

if __name__ == "__main__":
    (HERE / "start.html").write_text(HTML, encoding="utf-8")
    print("Saved start.html")
