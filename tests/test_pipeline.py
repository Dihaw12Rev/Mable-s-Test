# /// script
# requires-python = ">=3.10"
# dependencies = ["python-docx>=1.1", "openpyxl>=3.1"]
# ///
"""End-to-end check of analyze + render against the synthetic portal fixture."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fixture import snapshot  # noqa: E402
from hubspot_audit import analyze, graph, render, review, workflow_export  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> int:
    snap = snapshot()
    a = analyze.run(snap)

    print("\nCross-reference analysis")
    by_id = {w["id"]: w for w in a["workflows"]}
    props = {(p["object_type"], p["name"]): p for p in a["properties"]}

    check("all workflows analyzed", len(a["workflows"]) == 8, str(len(a["workflows"])))
    check("portal id resolved", a["portal_id"] == "12345678", a["portal_id"])

    mql = by_id["101"]
    check("writes detected on MQL flow",
          set(mql["properties_written"]) >= {"lifecyclestage", "mql_date"},
          str(mql["properties_written"]))
    check("reads detected on MQL flow",
          set(mql["properties_read"]) >= {"fit_score", "engagement_score"},
          str(mql["properties_read"]))
    check("workflow handoff detected", mql["workflows_triggered"] == ["102"],
          str(mql["workflows_triggered"]))
    check("suppression list captured", by_id["104"]["suppression_lists"] == ["9001"],
          str(by_id["104"]["suppression_lists"]))
    check("branch counted", mql["branch_count"] >= 1, str(mql["branch_count"]))
    check("unknown action type reported", "0-99" in a["unknown_action_types"],
          str(a["unknown_action_types"]))

    print("\nProperty usage index")
    owner = props[("contacts", "hubspot_owner_id")]
    check("owner property credited to both routing flows",
          set(owner["written_by_workflows"]) == {"102", "106"},
          str(owner["written_by_workflows"]))
    email = props[("contacts", "email")]
    check("email property credited to 3 forms", len(email["collected_by_forms"]) == 3,
          str(email["collected_by_forms"]))
    lifecycle = props[("contacts", "lifecyclestage")]
    check("lifecyclestage segmented by a list", lifecycle["segmented_by_lists"] == ["9002"],
          str(lifecycle["segmented_by_lists"]))
    dead = props[("contacts", "temp_import_flag_2023")]
    check("orphan custom property flagged unused", dead["unused"] is True)
    check("standard properties never flagged unused",
          all(not p["unused"] for p in a["properties"] if p["hubspot_defined"]))
    check("properties sorted by usage descending",
          a["properties"][0]["usage_score"] >= a["properties"][-1]["usage_score"])

    print("\nCoverage safety")
    check("full-coverage fixture reports usage as complete", a["usage_complete"] is True,
          str(a.get("coverage")))
    starved = snapshot()
    starved["workflows"] = []
    starved["forms"] = []
    starved["skipped"] = [
        {"endpoint": "/automation/v4/flows", "status": 403, "reason": "missing scope"},
        {"endpoint": "/marketing/v3/forms", "status": 403, "reason": "missing scope"},
    ]
    b = analyze.run(starved)
    check("missing sources mark usage incomplete", b["usage_complete"] is False, str(b["coverage"]))
    check("no property is called unused when sources are missing",
          not any(p["unused"] for p in b["properties"]),
          str([p["name"] for p in b["properties"] if p["unused"]][:5]))
    check("properties are marked usage-unknown instead",
          all(p["usage_known"] is False for p in b["properties"]))
    check("a genuinely orphan property is still flagged when coverage is complete",
          props[("contacts", "temp_import_flag_2023")]["unused"] is True)

    print("\nGrouping")
    systems = a["systems"]
    check("lifecycle system found", "Lifecycle & Stage Management" in systems, str(list(systems)))
    check("routing system found", "Lead Routing & Assignment" in systems)
    check("suppression system found", "Deliverability & Suppression" in systems)
    check("every workflow lands in exactly one system",
          sum(len(v) for v in systems.values()) == len(a["workflows"]))
    check("dependency cluster links MQL and routing flows",
          any({"101", "102"} <= set(c) for c in a["clusters"]), str(a["clusters"]))

    print("\nDescriptions")
    check("description mentions writes", "Writes" in mql["description"], mql["description"])
    check("description names the object", "contact workflow" in mql["description"])
    check("off workflows described as turned off",
          by_id["106"]["description"].startswith("Turned off"))

    print("\nWorkflow export merge")
    _check_export_merge()

    print("\nRendering")
    out = ROOT / "reports" / "_fixture"
    html = render.render_html(a, out / "sample.html")
    text = html.read_text()
    check("html written", html.exists() and len(text) > 20000, f"{len(text)} bytes")
    check("html carries a title", "<title>Sample Portal</title>" in text)
    check("json payload cannot close its host script tag", _payload_is_escaped(text))
    check("embedded json parses",
          _embedded_json_ok(text))
    check("no unsubstituted placeholders", "__ANALYSIS_JSON__" not in text and "__PORTAL_TITLE__" not in text)
    check("light palette defined on bare :root", ":root {" in text and "--ground: #FBF9F7" in text)
    check("dark palette defined for both stamped and unstamped",
          ':root:not([data-theme="light"])' in text and ':root[data-theme="dark"]' in text)
    check("body paints an explicit background", "background: var(--ground)" in text)

    docx = render.render_docx(a, out / "sample.docx")
    check("docx written", docx.exists() and docx.stat().st_size > 20000, f"{docx.stat().st_size} bytes")
    check("docx contains portal links", _docx_has_links(docx))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: " + ", ".join(FAILURES))
        return 1
    print("All checks passed.")
    return 0


def _check_export_merge() -> None:
    """The merge has three ways to silently corrupt the account picture. Lock all three.

    Excel hands ids back as floats, so a flow id has to survive the round trip or every
    row matches by name or not at all. A workflow the export cannot see must not have
    its enrolment invented as zero. And a workflow whose definition was never read must
    never reach the "empty, safe to delete" list — reading no steps is not the same as
    there being no steps.
    """
    import tempfile

    from openpyxl import Workbook

    header = ["Flow ID", "Name", "On or Off", "Object type", "Last action on",
              "Enrolled last 7-days", "Enrolled unique", "Currently Enrolled",
              "Current Issue Count", "Action type", "Trigger Type", "Created in"]
    rows = [
        # Ids as floats, exactly as openpyxl reads HubSpot's own file.
        [101.0, "MQL handoff", "true", "CONTACT", datetime(2020, 1, 2), 0.0, 40.0, 0.0, 0.0,
         "Send email; Set property value", "Filter criteria", "WORKFLOWS_APP"],
        [999.0, "Built after the snapshot", "true", "CONTACT", datetime(2026, 9, 1), 5.0,
         12.0, 3.0, 2.0, "Send email", "Events", "WORKFLOWS_APP"],
    ]
    book = Workbook()
    sheet = book.active
    sheet.append(header)
    for row in rows:
        sheet.append(row)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow-export.xlsx"
        book.save(path)

        snap = snapshot()
        before = len(snap["workflows"])
        report = workflow_export.merge(snap, path)

        check("flow id survives Excel's float round trip", report["matched"] == 1,
              f"matched {report['matched']}")
        check("a workflow the export does not know is added", report["added"] == 1)
        check("the rest are reported as absent from the export",
              report["missing_from_export"] == before - 1, str(report["missing_from_export"]))
        check("export date falls back to the newest row when the filename has none",
              report["exported_at"] == "2026-09-01", str(report["exported_at"]))

        merged = {str(w["id"]): w for w in snap["workflows"]}
        check("activity lands on the matched workflow",
              merged["101"]["_export_last_action_at"].startswith("2020-01-02"))
        check("enrolment is not invented for workflows the export never covered",
              all(w.get("_enrolled_total") is None
                  for wid, w in merged.items() if wid not in {"101", "999"}))

        a = analyze.run(snap)
        by_id = {w["id"]: w for w in a["workflows"]}
        added = by_id["999"]
        check("an export-only workflow says so rather than reading as empty",
              added["export_only"] and not added["definition_available"])
        check("its description is built from the export",
              any("Send email" in line for line in added["steps_text"]),
              " | ".join(added["steps_text"]))

        work = review.cohorts(a, graph.build(a))
        check("an unread definition never reaches the delete list",
              "999" not in {r["name"] for r in work["p1"]}
              and added["name"] not in {r["name"] for r in work["p1"]})
        check("a year without a run makes a live workflow stale",
              by_id["101"]["name"] in {r["name"] for r in work["p4"]})
        check("the stale reason cites the run date, not the edit date",
              any("2020-01-02" in r["reason"] for r in work["p4"] if r["name"] == by_id["101"]["name"]),
              str([r["reason"] for r in work["p4"] if r["name"] == by_id["101"]["name"]]))


def _payload_is_escaped(text: str) -> bool:
    """The embedded JSON must not contain a literal </ that would end the script element."""
    return "</" not in _payload(text)


def _payload(text: str) -> str:
    marker = '<script id="analysis" type="application/json">'
    start = text.index(marker) + len(marker)
    return text[start : text.index("</script>", start)]


def _embedded_json_ok(text: str) -> bool:
    raw = _payload(text).replace("<\\/", "</")
    try:
        json.loads(raw)
        return True
    except json.JSONDecodeError:
        return False


def _docx_has_links(path: Path) -> bool:
    import zipfile

    with zipfile.ZipFile(path) as z:
        rels = z.read("word/_rels/document.xml.rels").decode()
    return "app.hubspot.com/workflows/12345678" in rels


if __name__ == "__main__":
    raise SystemExit(main())
