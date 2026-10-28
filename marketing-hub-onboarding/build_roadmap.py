"""Build roadmap.html (the shareable visual roadmap) from process_data.py.

Run:  python3 build_roadmap.py
"""
import json
from pathlib import Path

import process_data as d

OUT = Path(__file__).with_name("roadmap.html")

data = {
    "programDays": d.PROGRAM_DAYS,
    "roles": d.ROLES,
    "phases": d.PHASES,
    "tasks": [dict(zip(["id", "phase", "task", "details", "owner", "client", "start", "due", "dep", "where", "auto"], t))
              for t in d.TASKS],
    "toolFit": [{"criterion": c, "work": w, "projects": p, "tickets": t} for c, w, p, t in d.TOOL_FIT],
    "verdict": d.TOOL_VERDICT,
    "questions": d.OPEN_QUESTIONS,
}

TEMPLATE = r"""<title>Marketing Hub Onboarding Roadmap</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column; the timeline and task tables scroll sideways inside their own boxes. */
:root {
  --bg: #f6f8fa; --surface: #ffffff; --fg: #17222e; --muted: #5b6876; --line: #dbe2e9;
  --navy: #1f3a5f; --accent: #2e7d7a; --accent-soft: #dcefea; --warn: #b4610e; --chip: #eef3f7;
  --display: "Bricolage Grotesque", "Segoe UI", system-ui, sans-serif;
  --body: "Instrument Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0f151c; --surface: #16202a; --fg: #e4ebf1; --muted: #98a6b4; --line: #2a3744;
  --navy: #9cc0e8; --accent: #5cc2bb; --accent-soft: #173a38; --warn: #f0a35a; --chip: #1e2a36; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0f151c; --surface: #16202a; --fg: #e4ebf1; --muted: #98a6b4; --line: #2a3744;
  --navy: #9cc0e8; --accent: #5cc2bb; --accent-soft: #173a38; --warn: #f0a35a; --chip: #1e2a36; color-scheme: dark }

body { background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15px; line-height: 1.55; }
.wrap { max-width: 1080px; margin: 0 auto; padding-block: 40px 72px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 48px; }
h1, h2, h3 { font-family: var(--display); color: var(--navy); text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: clamp(30px, 5vw, 44px); }
h2 { font-size: 24px; }
h3 { font-size: 18px; }
p { margin: 0; max-width: 68ch; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.muted { color: var(--muted); }
section { display: grid; gap: 18px; min-width: 0; }
header { display: grid; gap: 14px; }
.facts { display: flex; flex-wrap: wrap; gap: 8px 22px; font-family: var(--mono); font-size: 13px; color: var(--muted); }
.facts b { color: var(--fg); font-weight: 500; }

/* Timeline */
.scroll { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.gantt { min-width: 760px; padding: 14px 16px 18px; display: grid; gap: 6px; }
.grow { display: grid; grid-template-columns: 190px 1fr; align-items: center; gap: 12px; }
.glabel { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.glabel span { font-family: var(--mono); color: var(--muted); font-weight: 400; margin-right: 6px; }
.track { position: relative; height: 22px; }
.track .tick { position: absolute; top: -4px; bottom: -4px; border-left: 1px dashed var(--line); }
.bar { position: absolute; top: 3px; height: 16px; border-radius: 4px; background: var(--accent); }
.bar.pre { background: var(--muted); opacity: .55; }
.bar.post { background: repeating-linear-gradient(45deg, var(--accent), var(--accent) 6px, var(--accent-soft) 6px, var(--accent-soft) 12px); }
.axis .track { height: 18px; }
.axis .tlab { position: absolute; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; color: var(--muted); white-space: nowrap; }
.milestones { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 13px; color: var(--muted); }
.milestones b { font-family: var(--mono); color: var(--fg); font-weight: 500; }

/* Where it lives */
.tools { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.tool { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 8px; align-content: start; min-width: 0; }
.tool h3 { font-size: 16px; }
.score { display: flex; align-items: center; gap: 8px; font-family: var(--mono); font-size: 12px; color: var(--muted); }
.meter { flex: 1; height: 6px; background: var(--chip); border-radius: 3px; overflow: hidden; }
.meter i { display: block; height: 100%; background: var(--accent); }
details.fit summary { cursor: pointer; color: var(--accent); font-weight: 600; font-size: 14px; }
details.fit summary:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Tables */
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th { text-align: left; font-weight: 600; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .05em; padding: 8px 10px; border-bottom: 1px solid var(--line); }
td { padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
td.mono, .mono { font-family: var(--mono); font-size: 12.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.s0 { color: var(--warn); font-weight: 600; }

/* Filters */
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.filters .lab { font-size: 13px; color: var(--muted); margin-right: 4px; }
button.chip { font: inherit; font-size: 13px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); padding: 5px 12px; border-radius: 999px; cursor: pointer; }
button.chip[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: var(--bg); }

/* Phases */
.phase { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
.phase > summary { list-style: none; cursor: pointer; padding: 16px 18px; display: grid; grid-template-columns: auto 1fr auto; gap: 4px 14px; align-items: baseline; }
.phase > summary::-webkit-details-marker { display: none; }
.phase > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; border-radius: 10px; }
.pid { font-family: var(--mono); font-size: 13px; color: var(--accent); }
.pdays { font-family: var(--mono); font-size: 12.5px; color: var(--muted); white-space: nowrap; }
.pgoal { grid-column: 2 / 4; color: var(--muted); font-size: 14px; }
.pbody { padding: 0 18px 18px; display: grid; gap: 14px; min-width: 0; }
.kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.kv div { font-size: 14px; min-width: 0; }
.kv dt { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin-bottom: 2px; }
.kv dd { margin: 0; }
.owner { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 999px; background: var(--chip); white-space: nowrap; }
.cf { display: inline-block; font-size: 11px; font-weight: 600; color: var(--accent); background: var(--accent-soft); padding: 1px 6px; border-radius: 4px; margin-left: 6px; vertical-align: 1px; }
.task-d { color: var(--muted); font-size: 13px; margin-top: 2px; }
.empty { color: var(--muted); font-size: 14px; padding: 4px 0; }

ol.q { margin: 0; padding-left: 22px; display: grid; gap: 10px; max-width: 80ch; }
ol.q li span { display: block; font-size: 13px; color: var(--muted); }
footer { font-size: 13px; color: var(--muted); }
@media (max-width: 640px) {
  .phase > summary { grid-template-columns: auto 1fr; }
  .pdays { grid-column: 2; }
  .pgoal { grid-column: 1 / 3; }
}
@media (prefers-reduced-motion: no-preference) { .bar { transition: opacity .2s; } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">RevGravy · Draft v1 for review</div>
    <h1>Marketing Hub Onboarding Roadmap</h1>
    <p>Everything that happens after a customer buys a Marketing Hub onboarding, step by step from the FigJam session: the tasks, what we ask the customer, the technical setup, training, and where each piece should live in HubSpot.</p>
    <div class="facts" id="facts"></div>
  </header>

  <section aria-labelledby="t-time">
    <div class="eyebrow">Timeline</div>
    <h2 id="t-time">90 days from payment to "what's next"</h2>
    <p class="muted">Day 0 is when the deal reaches <i>Start Payment Received</i>. Grey is pre-sale; striped is post-program.</p>
    <div class="scroll"><div class="gantt" id="gantt"></div></div>
    <div class="milestones" id="milestones"></div>
  </section>

  <section aria-labelledby="t-tools">
    <div class="eyebrow">Work vs Projects vs Tickets</div>
    <h2 id="t-tools">Use each tool for the job it's best at</h2>
    <p class="muted">Your boss asked which one fits. They fit different jobs, so the recommendation is to use them together.</p>
    <div class="tools" id="tools"></div>
    <details class="fit">
      <summary>See the scoring (0 = poor, 1 = workable, 2 = strong)</summary>
      <div class="scroll" style="margin-top:12px"><table id="fit" style="min-width:720px"></table></div>
      <p class="muted" style="margin-top:8px;font-size:13px">HubSpot Work scores come from public beta descriptions (Oct 2026). Re-check once the portal is enrolled.</p>
    </details>
  </section>

  <section aria-labelledby="t-phases">
    <div class="eyebrow">Step by step</div>
    <h2 id="t-phases">Phases and tasks</h2>
    <div class="filters" id="filters" role="group" aria-label="Filter tasks"></div>
    <div id="phases" style="display:grid;gap:10px"></div>
  </section>

  <section aria-labelledby="t-q">
    <div class="eyebrow">Needs a decision</div>
    <h2 id="t-q">Open questions</h2>
    <ol class="q" id="questions"></ol>
  </section>

  <footer>Full detail (intake form questions, Marketing Hub tech setup checklist, training modules, comms plan and HubSpot build spec) is in <span class="mono">Marketing_Hub_Onboarding_Process.xlsx</span>. A ready-to-paste HubSpot Work prompt is in <span class="mono">hubspot-work-prompt.md</span>.</footer>
</div>

<script>
const D = __DATA__;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const dayLabel = (s, e) => s === e ? `Day ${s}` : `Day ${s}–${e}`;

// Facts
const post = D.tasks.filter(t => t.phase !== "P0");
$("facts").innerHTML = [
  [D.programDays + " days", "program"],
  [D.phases.length - 1, "post-sale phases"],
  [post.length, "post-sale tasks"],
  [post.filter(t => t.client === "Yes").length, "client-facing"],
  [D.questions.length, "open questions"],
].map(([n, l]) => `<span><b>${n}</b> ${l}</span>`).join("");

// Gantt: Day -30 .. 120 (post-program clipped at 120 and shown as continuing)
const MIN = -30, MAX = 120;
const pct = (d) => ((Math.max(MIN, Math.min(MAX, d)) - MIN) / (MAX - MIN)) * 100;
const ticks = [-30, 0, 30, 60, 90, 120];
const tickHtml = ticks.map(t => `<div class="tick" style="left:${pct(t)}%"></div>`).join("");
let g = `<div class="grow axis"><div></div><div class="track">${ticks.map(t => `<span class="tlab" style="left:${pct(t)}%">${t === 120 ? "120+" : "Day " + t}</span>`).join("")}</div></div>`;
for (const p of D.phases) {
  const cls = p.id === "P0" ? "bar pre" : p.id === "P9" ? "bar post" : "bar";
  g += `<div class="grow"><div class="glabel" title="${esc(p.name)}"><span>${p.id}</span>${esc(p.name)}</div>
    <div class="track">${tickHtml}<div class="${cls}" style="left:${pct(p.start)}%;width:${Math.max(1, pct(p.end) - pct(p.start))}%" title="${esc(p.name)}: ${dayLabel(p.start, p.end)}"></div></div></div>`;
}
$("gantt").innerHTML = g;
$("milestones").innerHTML = [
  ["Day 0", "paid → onboarding created, welcome email"], ["Day 1–3", "Phil ↔ Architect handoff"],
  ["Day 5–10", "15-min kickoff"], ["Fridays", "weekly update"], ["Day 30 / 60", "MBRs"],
  ["Day 60–65", "what's next call"], ["Day 80–88", "final results review"],
].map(([d, l]) => `<span><b>${d}</b> ${l}</span>`).join("");

// Tools
const totals = { work: 0, projects: 0, tickets: 0 };
for (const r of D.toolFit) { totals.work += r.work[0]; totals.projects += r.projects[0]; totals.tickets += r.tickets[0]; }
const max = D.toolFit.length * 2;
const key = { "HubSpot Work": "work", "Projects object": "projects", "Tickets": "tickets" };
$("tools").innerHTML = D.verdict.map(([tool, job]) => {
  const k = key[tool];
  const score = k ? `<div class="score"><div class="meter"><i style="width:${totals[k] / max * 100}%"></i></div>${totals[k]}/${max}</div>` : `<div class="score">Supporting</div>`;
  return `<div class="tool"><h3>${esc(tool)}</h3>${score}<p style="font-size:14px">${esc(job)}</p></div>`;
}).join("");
const cell = ([s, n]) => `<td><span class="${s === 0 ? "s0" : ""} mono">${s}</span> · ${esc(n)}</td>`;
$("fit").innerHTML = `<thead><tr><th>Criterion</th><th>HubSpot Work</th><th>Projects object</th><th>Tickets</th></tr></thead><tbody>` +
  D.toolFit.map(r => `<tr><td>${esc(r.criterion)}</td>${cell(r.work)}${cell(r.projects)}${cell(r.tickets)}</tr>`).join("") +
  `<tr><td><b>Total</b></td><td class="mono"><b>${totals.work}/${max}</b></td><td class="mono"><b>${totals.projects}/${max}</b></td><td class="mono"><b>${totals.tickets}/${max}</b></td></tr></tbody>`;

// Filters + phases
const owners = ["All", ...Object.keys(D.roles)];
let fOwner = "All", fClient = false;
function renderFilters() {
  $("filters").innerHTML = `<span class="lab">Owner</span>` +
    owners.map(o => `<button type="button" class="chip" data-o="${esc(o)}" aria-pressed="${o === fOwner}">${esc(o)}</button>`).join("") +
    `<span class="lab" style="margin-left:10px">View</span><button type="button" class="chip" id="cfbtn" aria-pressed="${fClient}">Client-facing only</button>`;
}
function renderPhases() {
  const open = new Set([...document.querySelectorAll("details.phase[open]")].map(e => e.dataset.p));
  if (!document.querySelector("details.phase")) open.add("P1");
  $("phases").innerHTML = D.phases.map(p => {
    const ts = D.tasks.filter(t => t.phase === p.id && (fOwner === "All" || t.owner === fOwner) && (!fClient || t.client === "Yes"));
    const rows = ts.map(t => `<tr><td class="mono">${t.id}</td><td>${esc(t.task)}${t.client === "Yes" ? '<span class="cf">Client</span>' : ""}<div class="task-d">${esc(t.details)}</div></td>
      <td><span class="owner">${esc(t.owner)}</span></td><td class="mono">${dayLabel(t.start, t.due)}</td><td style="font-size:13px">${esc(t.where)}${t.auto ? `<div class="task-d">⚙ ${esc(t.auto)}</div>` : ""}</td></tr>`).join("");
    const table = ts.length ? `<div class="scroll"><table style="min-width:760px"><thead><tr><th>ID</th><th>Task</th><th>Owner</th><th>When</th><th>Where / automation</th></tr></thead><tbody>${rows}</tbody></table></div>`
                            : `<div class="empty">No tasks match the current filter.</div>`;
    return `<details class="phase" data-p="${p.id}" ${open.has(p.id) ? "open" : ""}>
      <summary><span class="pid">${p.id}</span><h3>${esc(p.name)}</h3><span class="pdays">${dayLabel(p.start, p.end)} · ${ts.length} task${ts.length === 1 ? "" : "s"}</span><span class="pgoal">${esc(p.goal)}</span></summary>
      <div class="pbody"><dl class="kv"><div><dt>FigJam stage</dt><dd>${esc(p.figjam)}</dd></div><div><dt>What the client sees</dt><dd>${esc(p.client_sees)}</dd></div><div><dt>Done when</dt><dd>${esc(p.exit)}</dd></div></dl>${table}</div></details>`;
  }).join("");
}
$("filters").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.id === "cfbtn") fClient = !fClient; else fOwner = b.dataset.o;
  renderFilters(); renderPhases();
});
renderFilters(); renderPhases();

$("questions").innerHTML = D.questions.map(([t, q, w]) => `<li>${esc(q)}<span>${esc(t)} · changes: ${esc(w)}</span></li>`).join("");
</script>
"""

OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print(f"Saved {OUT}")
