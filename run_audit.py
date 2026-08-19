#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31", "python-dotenv>=1.0", "python-docx>=1.1", "weasyprint>=62"]
# ///
"""Document a HubSpot portal: extract, cross-reference, and report.

    uv run run_audit.py                     # full run against the live portal
    uv run run_audit.py --snapshot data/snapshot.json   # re-render without re-fetching

Every API call is read-only. Nothing here modifies the portal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hubspot_audit import analyze, extract, render  # noqa: E402
from hubspot_audit.client import Client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path("reports"), help="report output directory")
    parser.add_argument("--data", type=Path, default=Path("data"), help="raw snapshot directory")
    parser.add_argument("--snapshot", type=Path, help="re-render from an existing snapshot.json")
    parser.add_argument("--no-pdf", action="store_true", help="skip the PDF dashboard")
    parser.add_argument("--no-docx", action="store_true", help="skip the Word reference")
    parser.add_argument("--html", action="store_true",
                        help="also write the interactive HTML report")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    if args.snapshot:
        snapshot = json.loads(args.snapshot.read_text())
        print(f"Re-rendering from {args.snapshot}")
    else:
        snapshot = extract.extract_all(Client.from_env(), args.data)

    print("\nCross-referencing...")
    analysis = analyze.run(snapshot)
    args.data.mkdir(parents=True, exist_ok=True)
    (args.data / "analysis.json").write_text(json.dumps(analysis, indent=2, default=str))

    scored = [p for p in analysis["properties"] if p["usage_score"] > 0]
    print(
        f"  {len(analysis['workflows'])} workflows, "
        f"{len(analysis['properties'])} properties "
        f"({len(scored)} referenced by automation), "
        f"{len(analysis['systems'])} systems, "
        f"{len(analysis['clusters'])} dependency clusters"
    )

    outputs = []
    if not args.no_pdf:
        outputs.append(render.render_dashboard_pdf(
            analysis, args.out / "hubspot-portal-dashboard.pdf"))
    if not args.no_docx:
        outputs.append(render.render_docx(
            analysis, args.out / "hubspot-portal-reference.docx"))
    if args.html:
        outputs.append(render.render_html(
            analysis, args.out / "hubspot-portal-reference.html"))

    print("\nReports:")
    for path in outputs:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
