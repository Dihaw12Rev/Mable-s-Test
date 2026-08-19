# /// script
# requires-python = ">=3.10"
# dependencies = ["python-docx>=1.1"]
# ///
"""End-to-end check of analyze + render against the synthetic portal fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fixture import snapshot  # noqa: E402
from hubspot_audit import analyze, render  # noqa: E402

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
