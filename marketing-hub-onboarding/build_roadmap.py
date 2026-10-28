"""Build roadmap.html (the shareable visual roadmap) from process_data.py.

Run:  python3 build_roadmap.py
"""
import json
from pathlib import Path

import process_data as d

OUT = Path(__file__).with_name("roadmap.html")

data = {
    "planDays": d.PROGRAM_DAYS,
    "minDays": d.PROGRAM_MIN_DAYS,
    "fixedUntil": d.FIXED_UNTIL_DAY,
    "roles": d.ROLES,
    "decisions": d.DECISIONS,
    "phases": d.PHASES,
    "tasks": [dict(zip(["id", "phase", "task", "details", "owner", "client", "start", "due", "dep", "where", "repeats"], t))
              for t in d.TASKS],
    "where": d.WHERE_IT_LIVES,
    "factories": d.FACTORIES,
    "requestRules": d.REQUEST_RULES,
    "requestClasses": d.REQUEST_CLASSES,
    "scope": d.SCOPE_LIMITS,
    "post": d.POST_PROGRAM,
    "questions": d.OPEN_QUESTIONS,
}

TEMPLATE = r"""<title>Marketing Hub Onboarding Roadmap</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column; the timeline and tables scroll sideways inside their own boxes. */
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
  display: grid; gap: 52px; }
h1, h2, h3 { font-family: var(--display); color: var(--navy); text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: clamp(30px, 5vw, 44px); }
h2 { font-size: 24px; }
h3 { font-size: 18px; }
p { margin: 0; max-width: 68ch; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.muted { color: var(--muted); }
section { display: grid; gap: 16px; min-width: 0; }
header { display: grid; gap: 14px; }
.facts { display: flex; flex-wrap: wrap; gap: 8px 22px; font-family: var(--mono); font-size: 13px; color: var(--muted); }
.facts b { color: var(--fg); font-weight: 500; }
.box { border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.scroll { overflow-x: auto; }

/* Program length switch */
.switch { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 3px; background: var(--surface); gap: 2px; }
.switch button { font: inherit; font-size: 13px; border: 0; background: transparent; color: var(--fg); padding: 5px 14px; border-radius: 999px; cursor: pointer; font-variant-numeric: tabular-nums; }
.switch button[aria-pressed="true"] { background: var(--navy); color: var(--bg); }
.row { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; }

/* Timeline */
.gantt { min-width: 760px; padding: 14px 16px 18px; display: grid; gap: 6px; }
.grow { display: grid; grid-template-columns: 190px 1fr; align-items: center; gap: 12px; }
.glabel { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.glabel span { font-family: var(--mono); color: var(--muted); font-weight: 400; margin-right: 6px; }
.track { position: relative; height: 22px; }
.track .tick { position: absolute; top: -4px; bottom: -4px; border-left: 1px dashed var(--line); }
.track .end { position: absolute; top: -6px; bottom: -6px; border-left: 2px solid var(--warn); }
.bar { position: absolute; top: 3px; height: 16px; border-radius: 4px; background: var(--accent); }
.bar.pre { background: var(--muted); opacity: .55; }
.bar.post { background: repeating-linear-gradient(45deg, var(--accent), var(--accent) 6px, var(--accent-soft) 6px, var(--accent-soft) 12px); }
.axis .track { height: 18px; }
.axis .tlab { position: absolute; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; color: var(--muted); white-space: nowrap; }
.milestones { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 13px; color: var(--muted); }
.milestones b { font-family: var(--mono); color: var(--fg); font-weight: 500; font-variant-numeric: tabular-nums; }

/* Cards */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.card { padding: 16px; display: grid; gap: 6px; align-content: start; min-width: 0; }
.card h3 { font-size: 16px; }
.card p { font-size: 14px; }
.card.off h3 { color: var(--muted); }
.price { font-family: var(--mono); font-size: 12.5px; color: var(--accent); }

/* Tables */
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th { text-align: left; font-weight: 600; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .05em; padding: 8px 10px; border-bottom: 1px solid var(--line); }
td { padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
.mono { font-family: var(--mono); font-size: 12.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.sub { color: var(--muted); font-size: 13px; margin-top: 2px; }
.tag { display: inline-block; font-size: 11px; font-weight: 600; padding: 1px 6px; border-radius: 4px; background: var(--chip); color: var(--muted); white-space: nowrap; }
.tag.core { background: var(--accent-soft); color: var(--accent); }
.urg { font-weight: 600; white-space: nowrap; }
.urg.Critical { color: var(--warn); }

/* Filters */
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.filters .lab { font-size: 13px; color: var(--muted); margin-right: 4px; }
button.chip { font: inherit; font-size: 13px; border: 1px solid var(--line); background: var(--surface); color: var(--fg); padding: 5px 12px; border-radius: 999px; cursor: pointer; }
button.chip[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: var(--bg); }
button:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Phases */
.phase > summary { list-style: none; cursor: pointer; padding: 16px 18px; display: grid; grid-template-columns: auto 1fr auto; gap: 4px 14px; align-items: baseline; }
.phase > summary::-webkit-details-marker { display: none; }
.pid { font-family: var(--mono); font-size: 13px; color: var(--accent); }
.pdays { font-family: var(--mono); font-size: 12.5px; color: var(--muted); white-space: nowrap; }
.pgoal { grid-column: 2 / 4; color: var(--muted); font-size: 14px; }
.pbody { padding: 0 18px 18px; display: grid; gap: 14px; min-width: 0; }
.kv { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 0; }
.kv div { font-size: 14px; min-width: 0; }
.kv dt { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin-bottom: 2px; }
.kv dd { margin: 0; }
.owner { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 999px; background: var(--chip); white-space: nowrap; }
.cf { display: inline-block; font-size: 11px; font-weight: 600; color: var(--accent); background: var(--accent-soft); padding: 1px 6px; border-radius: 4px; margin-left: 6px; vertical-align: 1px; }
.empty { color: var(--muted); font-size: 14px; padding: 4px 0; }
ul.rules { margin: 0; padding-left: 20px; display: grid; gap: 4px; font-size: 14px; max-width: 80ch; }
ol.q { margin: 0; padding-left: 22px; display: grid; gap: 10px; max-width: 80ch; }
ol.q li span { display: block; font-size: 13px; color: var(--muted); }
footer { font-size: 13px; color: var(--muted); }
@media (max-width: 640px) {
  .phase > summary { grid-template-columns: auto 1fr; }
  .pdays { grid-column: 2; }
  .pgoal { grid-column: 1 / 3; }
}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">RevGravy · v2 after review</div>
    <h1>Marketing Hub Onboarding Roadmap</h1>
    <p>Everything that happens after a customer buys a Marketing Hub onboarding, from the FigJam session and the answers from review. It all runs in HubSpot Work; the customer sees it through Supered.</p>
    <div class="facts" id="facts"></div>
  </header>

  <section aria-labelledby="t-dec">
    <div class="eyebrow">Decided</div>
    <h2 id="t-dec">What the review settled</h2>
    <div class="box scroll"><table id="decisions" style="min-width:680px"></table></div>
  </section>

  <section aria-labelledby="t-time">
    <div class="eyebrow">Timeline</div>
    <h2 id="t-time">From payment to "what's next"</h2>
    <div class="row">
      <span class="muted" style="font-size:14px">Program length</span>
      <div class="switch" id="len" role="group" aria-label="Program length"></div>
    </div>
    <p class="muted" style="font-size:14px">Day 0 is when the deal reaches <i>Start Payment Received</i>. Week one stays the same for every program; later dates compress for shorter programs. The orange line is the program's end.</p>
    <div class="box scroll"><div class="gantt" id="gantt"></div></div>
    <div class="milestones" id="milestones"></div>
  </section>

  <section aria-labelledby="t-where">
    <div class="eyebrow">Where it lives</div>
    <h2 id="t-where">HubSpot Work runs it, Supered shows it</h2>
    <div class="cards" id="where"></div>
  </section>

  <section aria-labelledby="t-phases">
    <div class="eyebrow">Step by step</div>
    <h2 id="t-phases">Sections and tasks</h2>
    <p class="muted" style="font-size:14px">These are the sections of the HubSpot Work template. Dates follow the program length above.</p>
    <div class="filters" id="filters" role="group" aria-label="Filter tasks"></div>
    <div id="phases" style="display:grid;gap:10px"></div>
  </section>

  <section aria-labelledby="t-fac">
    <div class="eyebrow">Progress measures</div>
    <h2 id="t-fac">The standard Factories for Marketing Hub</h2>
    <p class="muted" style="font-size:14px">Named like the existing records, e.g. "&lt;Client&gt; 1.1 Visitor to Lead". Core ones go into every program.</p>
    <div class="box scroll"><table id="factories" style="min-width:720px"></table></div>
  </section>

  <section aria-labelledby="t-req">
    <div class="eyebrow">Requests</div>
    <h2 id="t-req">$250 per request, handled by urgency</h2>
    <ul class="rules" id="rules"></ul>
    <div class="box scroll"><table id="classes" style="min-width:720px"></table></div>
    <h3 style="margin-top:8px">Scope limits for the new in-scope work</h3>
    <div class="cards" id="scope"></div>
  </section>

  <section aria-labelledby="t-post">
    <div class="eyebrow">After the program</div>
    <h2 id="t-post">6 months free, then a paid next step</h2>
    <div class="cards" id="post"></div>
  </section>

  <section aria-labelledby="t-q">
    <div class="eyebrow">Still open</div>
    <h2 id="t-q">Questions left</h2>
    <ol class="q" id="questions"></ol>
  </section>

  <footer>Full detail (intake form, Pro &amp; Enterprise tech setup, training, comms, HubSpot Work setup) is in <span class="mono">Marketing_Hub_Onboarding_Process.xlsx</span>. The exact HubSpot Work prompt is in <span class="mono">hubspot-work-prompt.txt</span>.</footer>
</div>

<script>
const D = __DATA__;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let LEN = D.planDays;

// Same rule as process_data.scaled_due()
const scale = (phase, day) => {
  if (phase === "P0" || day <= D.fixedUntil) return day;
  if (phase === "P9") return day - D.planDays + LEN;
  return Math.floor(day * LEN / D.planDays + 0.5);
};
const dayLabel = (s, e) => s === e ? `Day ${s}` : `Day ${s}–${e}`;

const post = D.tasks.filter(t => t.phase !== "P0");
$("facts").innerHTML = [
  [`${D.minDays}–${D.planDays} days`, "program"],
  [D.phases.length, "sections"],
  [D.tasks.length, "tasks"],
  [post.filter(t => t.client === "Yes").length, "client-facing"],
  [D.questions.length, "open questions"],
].map(([n, l]) => `<span><b>${n}</b> ${l}</span>`).join("");

$("decisions").innerHTML = `<thead><tr><th>Topic</th><th>Answer</th><th>What changed</th></tr></thead><tbody>` +
  D.decisions.map(([t, a, w]) => `<tr><td style="font-weight:600;white-space:nowrap">${esc(t)}</td><td>${esc(a)}</td><td class="sub" style="margin:0">${esc(w)}</td></tr>`).join("") + `</tbody>`;

// Program length switch
$("len").innerHTML = [60, 75, 90].map(n => `<button type="button" data-n="${n}" aria-pressed="${n === LEN}">${n} days</button>`).join("");
$("len").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  LEN = +b.dataset.n;
  [...$("len").children].forEach(x => x.setAttribute("aria-pressed", String(+x.dataset.n === LEN)));
  renderTimeline(); renderPhases();
});

function renderTimeline() {
  const MIN = -30, MAX = 120;
  const pct = (d) => ((Math.max(MIN, Math.min(MAX, d)) - MIN) / (MAX - MIN)) * 100;
  const ticks = [-30, 0, 30, 60, 90, 120];
  const tickHtml = ticks.map(t => `<div class="tick" style="left:${pct(t)}%"></div>`).join("") + `<div class="end" style="left:${pct(LEN)}%" title="Program ends: Day ${LEN}"></div>`;
  let g = `<div class="grow axis"><div></div><div class="track">${ticks.map(t => `<span class="tlab" style="left:${pct(t)}%">${t === 120 ? "120+" : "Day " + t}</span>`).join("")}</div></div>`;
  for (const p of D.phases) {
    const s = scale(p.id, p.start), e = scale(p.id, p.end);
    const cls = p.id === "P0" ? "bar pre" : p.id === "P9" ? "bar post" : "bar";
    g += `<div class="grow"><div class="glabel" title="${esc(p.name)}"><span>${p.id}</span>${esc(p.name)}</div>
      <div class="track">${tickHtml}<div class="${cls}" style="left:${pct(s)}%;width:${Math.max(1, pct(e) - pct(s))}%" title="${esc(p.name)}: ${dayLabel(s, e)}"></div></div></div>`;
  }
  $("gantt").innerHTML = g;
  const T = (id) => D.tasks.find(t => t.id === id);
  const at = (id, which = "due") => scale(T(id).phase, T(id)[which]);
  $("milestones").innerHTML = [
    ["Day 0", "paid, welcome email"], [`Day ${at("1.05", "start")}–${at("1.05")}`, "Phil → Architect handoff"],
    [`Day ${at("3.02", "start")}–${at("3.02")}`, "15-min kickoff"], ["Fridays", "weekly update"],
    [`Day ${at("4.11")}`, "foundations done"], [`Day ${scale("P8", 60)}–${at("8.02")}`, "what's next call"],
    [`Day ${at("8.05")}`, "program ends"], [`Day ${at("9.05")}`, "free monitoring ends"],
  ].map(([d, l]) => `<span><b>${d}</b> ${l}</span>`).join("");
}

$("where").innerHTML = D.where.map(([t, j]) => `<div class="box card${t.startsWith("Not") ? " off" : ""}"><h3>${esc(t)}</h3><p>${esc(j)}</p></div>`).join("");

// Phases
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
    const when = (t) => t.phase === "P0" ? "Before Day 0" : dayLabel(scale(t.phase, t.start), scale(t.phase, t.due));
    const rows = ts.map(t => `<tr><td class="mono">${t.id}</td><td>${esc(t.task)}${t.client === "Yes" ? '<span class="cf">Client</span>' : ""}<div class="sub">${esc(t.details)}</div></td>
      <td><span class="owner">${esc(t.owner)}</span></td><td class="mono">${when(t)}${t.repeats ? `<div class="sub" style="font-family:var(--body)">${esc(t.repeats)}</div>` : ""}</td><td style="font-size:13px">${esc(t.where)}</td></tr>`).join("");
    const table = ts.length ? `<div class="scroll"><table style="min-width:760px"><thead><tr><th>ID</th><th>Task</th><th>Owner</th><th>When</th><th>Lives in</th></tr></thead><tbody>${rows}</tbody></table></div>`
                            : `<div class="empty">No tasks match the current filter.</div>`;
    const ps = scale(p.id, p.start), pe = scale(p.id, p.end);
    return `<details class="phase box" data-p="${p.id}" ${open.has(p.id) ? "open" : ""}>
      <summary><span class="pid">${p.id}</span><h3>${esc(p.name)}</h3><span class="pdays">${p.id === "P0" ? "Before Day 0" : dayLabel(ps, pe)} · ${ts.length} task${ts.length === 1 ? "" : "s"}</span><span class="pgoal">${esc(p.goal)}</span></summary>
      <div class="pbody"><dl class="kv"><div><dt>FigJam stage</dt><dd>${esc(p.figjam)}</dd></div><div><dt>What the client sees</dt><dd>${esc(p.client_sees)}</dd></div><div><dt>Done when</dt><dd>${esc(p.exit)}</dd></div></dl>${table}</div></details>`;
  }).join("");
}
$("filters").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.id === "cfbtn") fClient = !fClient; else fOwner = b.dataset.o;
  renderFilters(); renderPhases();
});

$("factories").innerHTML = `<thead><tr><th>ID</th><th>Progress measure</th><th>When</th><th>What it measures</th><th>Built by</th></tr></thead><tbody>` +
  D.factories.map(([id, n, w, m, r, b]) => `<tr><td class="mono">${id}</td><td style="font-weight:600">${esc(n)}</td><td><span class="tag${w === "Every customer" ? " core" : ""}">${w === "Every customer" ? "Core" : "Optional"}</span><div class="sub">${esc(w)}</div></td><td>${esc(m)}<div class="sub">${esc(r)}</div></td><td class="mono">${esc(b)}</td></tr>`).join("") + `</tbody>`;

$("rules").innerHTML = D.requestRules.map(r => `<li>${esc(r)}</li>`).join("");
$("classes").innerHTML = `<thead><tr><th>Urgency</th><th>What it is</th><th>Response</th><th>Price</th></tr></thead><tbody>` +
  D.requestClasses.map(([u, w, t, p]) => `<tr><td class="urg ${u.replace(/\s/g, "")}">${esc(u)}</td><td>${esc(w)}</td><td>${esc(t)}</td><td>${esc(p)}</td></tr>`).join("") + `</tbody>`;
$("scope").innerHTML = D.scope.map(([a, l]) => `<div class="box card"><h3>${esc(a)}</h3><p>${esc(l)}</p></div>`).join("");

$("post").innerHTML = D.post.map(([o, p, w]) => `<div class="box card"><h3>${esc(o)}</h3><div class="price">${esc(p)}</div><p>${esc(w)}</p></div>`).join("");

$("questions").innerHTML = D.questions.map(([t, q, w]) => `<li>${esc(q)}<span>${esc(t)} · changes: ${esc(w)}</span></li>`).join("");

renderTimeline(); renderFilters(); renderPhases();
</script>
"""

OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print(f"Saved {OUT}")
