"""Build journey.html: the start-to-end onboarding experience, lane by lane, from process_data.py.

Run:  python3 build_journey.py
"""
import json
from datetime import date, timedelta
from pathlib import Path

import process_data as d

OUT = Path(__file__).with_name("journey.html")
DAY0 = date.fromisoformat(d.EXAMPLE["day0"])
TASK = {t[0]: t[2] for t in d.TASKS}


def on(day):
    return DAY0 + timedelta(days=day)


def fmt(dt, weekday=False, year=False):
    out = f"{dt:%b} {dt.day}"
    if weekday:
        out = f"{dt:%a} " + out
    if year:
        out += f", {dt.year}"
    return out


def date_label(s, e):
    a, b = on(s), on(e)
    if s == e:
        return fmt(a, weekday=True, year=a.year != DAY0.year)
    return f"{fmt(a, year=a.year != b.year)} – {fmt(b, year=b.year != DAY0.year)}"


def day_label(s, e):
    if e < 0:
        return "Before Day 0"
    return f"Day {s}" if s == e else f"Day {s}–{e}"


moments = []
for m in d.JOURNEY:
    moments.append({**m, "days": day_label(m["start"], m["end"]), "dates": date_label(m["start"], m["end"]),
                    "done": [[i, TASK[i]] for i in m["done"]], "wont": [[i, TASK[i]] for i in m.get("wont", [])]})

data = {
    "example": {**d.EXAMPLE, "day0Label": fmt(DAY0, weekday=True, year=True),
                "endLabel": fmt(on(d.EXAMPLE["program_days"]), weekday=True, year=True)},
    "lanes": d.LANES,
    "moments": moments,
    "status": d.STATUS_RULES,
    "requests": d.REQUEST_FLOW,
    "rhythm": d.WEEKLY_RHYTHM,
    "exceptions": d.EXCEPTIONS,
}

TEMPLATE = r"""<title>Onboarding Journey</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: a dated rail on the left, five swimlanes per moment on the right; lanes stack on phones. */
:root {
  --bg: #f6f8fa; --surface: #ffffff; --fg: #17222e; --muted: #5b6876; --line: #dbe2e9; --chip: #eef3f7;
  --navy: #1f3a5f; --accent: #2e7d7a; --accent-soft: #dcefea;
  --l-customer: #2e7d7a; --l-phil: #1f3a5f; --l-architect: #a85a0c; --l-ops: #5b6876; --l-work: #6a4bb5;
  --display: "Bricolage Grotesque", "Segoe UI", system-ui, sans-serif;
  --body: "Instrument Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0f151c; --surface: #16202a; --fg: #e4ebf1; --muted: #98a6b4; --line: #2a3744; --chip: #1e2a36;
  --navy: #9cc0e8; --accent: #5cc2bb; --accent-soft: #173a38;
  --l-customer: #5cc2bb; --l-phil: #9cc0e8; --l-architect: #f0a35a; --l-ops: #a7b4c2; --l-work: #b59cf0; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0f151c; --surface: #16202a; --fg: #e4ebf1; --muted: #98a6b4; --line: #2a3744; --chip: #1e2a36;
  --navy: #9cc0e8; --accent: #5cc2bb; --accent-soft: #173a38;
  --l-customer: #5cc2bb; --l-phil: #9cc0e8; --l-architect: #f0a35a; --l-ops: #a7b4c2; --l-work: #b59cf0; color-scheme: dark }

body { background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15px; line-height: 1.55; }
.wrap { max-width: 1240px; margin: 0 auto; padding-block: 40px 72px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 48px; }
h1, h2, h3 { font-family: var(--display); color: var(--navy); text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: clamp(30px, 5vw, 44px); }
h2 { font-size: 24px; }
h3 { font-size: 18px; }
p { margin: 0; max-width: 70ch; }
.eyebrow { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.muted { color: var(--muted); }
section { display: grid; gap: 16px; min-width: 0; }
header { display: grid; gap: 14px; }
.box { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
.mono { font-family: var(--mono); font-size: 12.5px; font-variant-numeric: tabular-nums; }

/* Example customer */
.example { padding: 16px 18px; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px 20px; }
.example div { min-width: 0; font-size: 14px; }
.example dt { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
.example dd { margin: 0; }
.example .tag { grid-column: 1 / -1; font-size: 13px; color: var(--muted); }

/* Lane switch */
.lens { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.lens .lab { font-size: 13px; color: var(--muted); margin-right: 4px; }
.lens button { font: inherit; font-size: 13px; border: 1px solid var(--line); background: var(--surface); color: var(--fg);
  padding: 5px 12px 5px 10px; border-radius: 999px; cursor: pointer; display: inline-flex; align-items: center; gap: 7px; }
.lens button[aria-pressed="true"] { background: var(--navy); border-color: var(--navy); color: var(--bg); }
.dot { width: 9px; height: 9px; border-radius: 50%; flex: none; background: var(--lc, var(--muted)); }
button:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.lanehelp { font-size: 14px; color: var(--muted); min-height: 1.5em; }

/* Moments */
.stagehead { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); padding-top: 8px; }
.moments { display: grid; gap: 12px; }
.moment { display: grid; grid-template-columns: 150px 1fr; gap: 0; overflow: hidden; }
.when { padding: 16px; border-right: 1px solid var(--line); display: grid; align-content: start; gap: 4px; }
.when .d { font-family: var(--mono); font-size: 14px; font-weight: 500; color: var(--fg); font-variant-numeric: tabular-nums; }
.when .c { font-size: 13px; color: var(--muted); }
.body { padding: 16px 18px; display: grid; gap: 14px; min-width: 0; }
.lanes { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.lanes.one { grid-template-columns: minmax(0, 1fr); }
.lane { border-top: 3px solid var(--lc); padding-top: 8px; min-width: 0; }
.lane h4 { margin: 0 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--lc); font-weight: 600; }
.lane ul { margin: 0; padding-left: 16px; display: grid; gap: 6px; font-size: 13.5px; }
.lane.empty { opacity: .45; }
.lane.empty p { font-size: 13px; color: var(--muted); }
.lanes.one .lane ul { font-size: 14.5px; }
details.done summary { cursor: pointer; font-size: 13px; color: var(--accent); font-weight: 600; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.chip { font-size: 12.5px; padding: 2px 8px; border-radius: 6px; background: var(--accent-soft); color: var(--fg); }
.chip b { font-family: var(--mono); font-weight: 500; color: var(--accent); margin-right: 4px; }
.chip.wont { background: var(--chip); color: var(--muted); }
.chip.wont b { color: var(--muted); }
.note { font-size: 13px; color: var(--l-architect); border-left: 2px solid var(--l-architect); padding-left: 10px; }

/* Reference sections */
.cols2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th { text-align: left; font-weight: 600; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .05em; padding: 8px 12px; border-bottom: 1px solid var(--line); }
td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
.who { display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; font-weight: 600; font-size: 13px; }
ol.flow { margin: 0; padding: 0; list-style: none; display: grid; gap: 0; counter-reset: f; }
ol.flow li { counter-increment: f; display: grid; grid-template-columns: 34px 1fr; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--line); }
ol.flow li:last-child { border-bottom: 0; }
ol.flow li::before { content: counter(f); font-family: var(--mono); font-size: 13px; color: var(--accent); background: var(--accent-soft); border-radius: 50%; width: 26px; height: 26px; display: grid; place-items: center; }
ol.flow b { display: block; }
ol.flow span { color: var(--muted); font-size: 14px; }
.status { padding: 14px 16px; display: grid; gap: 10px; }
.status div { display: grid; grid-template-columns: 150px 1fr; gap: 12px; font-size: 14px; align-items: baseline; }
.pill { display: inline-block; font-size: 12.5px; font-weight: 600; padding: 2px 10px; border-radius: 999px; background: var(--chip); justify-self: start; }
.pill.Done { background: var(--accent-soft); color: var(--accent); }
.pill.Waiting { color: var(--l-architect); }
.card { padding: 14px 16px; display: grid; gap: 6px; align-content: start; }
.card h3 { font-size: 15.5px; }
.card p { font-size: 14px; color: var(--muted); }
footer { font-size: 13px; color: var(--muted); }

@media (max-width: 1000px) {
  .lanes { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
}
@media (max-width: 640px) {
  .moment { grid-template-columns: 1fr; }
  .when { border-right: 0; border-bottom: 1px solid var(--line); grid-template-columns: auto 1fr; align-items: baseline; gap: 4px 12px; padding: 12px 16px; }
  .lanes { grid-template-columns: 1fr; }
  .lane.empty { display: none; }
  .status div { grid-template-columns: 1fr; gap: 4px; }
}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">RevGravy · Marketing Hub Onboarding</div>
    <h1>Onboarding Journey</h1>
    <p>One customer, start to end: what the customer experiences, what Phil, the Architect and Ops do, and what changes in HubSpot Work at each moment. Also covers when tasks get marked Done, how requests flow, and the 6 months after the program.</p>
    <dl class="box example" id="example"></dl>
  </header>

  <section aria-labelledby="t-journey">
    <h2 id="t-journey">From sale to month 6</h2>
    <div class="lens" id="lens" role="group" aria-label="Whose view"></div>
    <p class="lanehelp" id="lanehelp"></p>
    <div class="moments" id="moments"></div>
  </section>

  <section aria-labelledby="t-week">
    <div class="eyebrow">Day 7 to the end</div>
    <h2 id="t-week">A normal week</h2>
    <div class="box scroll"><table id="rhythm" style="min-width:560px"></table></div>
  </section>

  <section aria-labelledby="t-req">
    <div class="eyebrow">Any time</div>
    <h2 id="t-req">How a request moves</h2>
    <ol class="box flow" id="requests"></ol>
  </section>

  <section aria-labelledby="t-status">
    <div class="eyebrow">In HubSpot Work</div>
    <h2 id="t-status">When to change a task's status</h2>
    <p class="muted" style="font-size:14px">The Architect keeps every status current, including the customer's own tasks. The customer never touches HubSpot Work.</p>
    <div class="box status" id="status"></div>
  </section>

  <section aria-labelledby="t-what">
    <div class="eyebrow">Real life</div>
    <h2 id="t-what">When things don't go to plan</h2>
    <div class="cols2" id="exceptions"></div>
  </section>

  <footer>Dates assume a 90-day program starting on the example's Day 0. For a 60- or 75-day program, week one stays the same and later dates compress. Task IDs match the HubSpot Work template and the sheet.</footer>
</div>

<script>
const D = __DATA__;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const laneColor = (k) => `--lc: var(--l-${k})`;
const LANE = Object.fromEntries(D.lanes.map(([k, n, h]) => [k, { name: n, help: h }]));

const E = D.example;
$("example").innerHTML = [
  ["Example customer", E.customer], ["Hub", E.tier], ["Program", `${E.program_days} days`],
  ["Day 0", E.day0Label], ["Program ends", E.endLabel], ["Progress measures", E.measures], ["Moving from", E.migration],
].map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("") + `<div class="tag">${esc(E.note)}</div>`;

let lens = "all";
function renderLens() {
  $("lens").innerHTML = `<span class="lab">Whose view</span>` +
    [["all", "Everyone"], ...D.lanes.map(([k, n]) => [k, n])].map(([k, n]) =>
      `<button type="button" data-k="${k}" aria-pressed="${k === lens}" style="${k === "all" ? "" : laneColor(k)}">${k === "all" ? "" : '<span class="dot"></span>'}${esc(n)}</button>`).join("");
  $("lanehelp").textContent = lens === "all" ? "Each moment shows all five lanes. Pick one to read it as that person's script." : LANE[lens].help;
}
$("lens").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  lens = b.dataset.k; renderLens(); renderMoments();
});

function laneHtml(k, items) {
  const head = `<h4>${esc(LANE[k].name)}</h4>`;
  if (!items.length) return `<div class="lane empty" style="${laneColor(k)}">${head}<p>Nothing here</p></div>`;
  return `<div class="lane" style="${laneColor(k)}">${head}<ul>${items.map(i => `<li>${esc(i)}</li>`).join("")}</ul></div>`;
}

function renderMoments() {
  let html = "", lastStage = "";
  const shown = D.moments.filter(m => lens === "all" || m[lens].length);
  for (const m of shown) {
    if (m.stage !== lastStage) { html += `<div class="stagehead">${esc(m.stage)}</div>`; lastStage = m.stage; }
    const lanes = lens === "all" ? D.lanes.map(([k]) => laneHtml(k, m[k])).join("") : laneHtml(lens, m[lens]);
    const n = m.done.length + m.wont.length;
    const done = n ? `<details class="done"><summary>Mark Done in HubSpot Work: ${m.done.length} task${m.done.length === 1 ? "" : "s"}${m.wont.length ? ` · Won't do: ${m.wont.length}` : ""}</summary><div class="chips">` +
      m.done.map(([i, t]) => `<span class="chip"><b>${i}</b>${esc(t)}</span>`).join("") +
      m.wont.map(([i, t]) => `<span class="chip wont"><b>${i}</b>${esc(t)} · Won't do</span>`).join("") + `</div></details>` : "";
    html += `<article class="box moment"><div class="when"><span class="d">${esc(m.days)}</span><span class="c">${esc(m.dates)}</span></div>
      <div class="body"><h3>${esc(m.title)}</h3><div class="lanes${lens === "all" ? "" : " one"}">${lanes}</div>${m.note ? `<p class="note">${esc(m.note)}</p>` : ""}${done}</div></article>`;
  }
  $("moments").innerHTML = html;
}

const whoKey = (w) => w.startsWith("HubSpot") ? "work" : w.startsWith("Customer") ? "customer" : w.startsWith("Phil") ? "phil" : "architect";
$("rhythm").innerHTML = `<thead><tr><th>When</th><th>Who</th><th>What happens</th></tr></thead><tbody>` +
  D.rhythm.map(([w, who, what]) => `<tr><td class="mono" style="white-space:nowrap">${esc(w)}</td><td><span class="who" style="${laneColor(whoKey(who))}"><span class="dot"></span>${esc(who)}</span></td><td>${esc(what)}</td></tr>`).join("") + `</tbody>`;

$("requests").innerHTML = D.requests.map(([h, t]) => `<li><div><b>${esc(h)}</b><span>${esc(t)}</span></div></li>`).join("");
$("status").innerHTML = D.status.map(([s, t]) => `<div><span class="pill ${esc(s.split(" ")[0])}">${esc(s)}</span><span>${esc(t)}</span></div>`).join("");
$("exceptions").innerHTML = D.exceptions.map(([h, t]) => `<div class="box card"><h3>${esc(h)}</h3><p>${esc(t)}</p></div>`).join("");

renderLens(); renderMoments();
</script>
"""

OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print(f"Saved {OUT}")
