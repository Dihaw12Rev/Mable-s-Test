#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31", "python-dotenv>=1.0"]
# ///
"""Delete HubSpot workflows from a signed-off manifest. Irreversible.

    uv run delete_workflows.py --manifest FILE --dry-run          # default: changes nothing
    uv run delete_workflows.py --manifest FILE --tier GREEN --limit 1 --confirm-delete
    uv run delete_workflows.py --manifest FILE --tier GREEN --confirm-delete

HubSpot has no recycle bin. A deleted workflow is gone and its logic with it, so this
script is built to be hard to misfire:

* It deletes by **workflow id**, never by name. Names are not unique in this portal —
  thirteen workflows share the name "Send a follow-up email after form submission",
  seven of them live — so a name-driven delete would take out running automation.
* Every id is **re-fetched from HubSpot immediately before deletion** and re-checked:
  still exists, name still matches, and still in the on/off state the manifest recorded
  for it. Anything that moved since sign-off is skipped, not deleted.
* Nothing runs without `--confirm-delete`. Without it this is a read-only rehearsal.
* Every outcome is appended to a JSONL log as it happens, so an interrupted run leaves
  a complete record of what did and did not go.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE = "https://api.hubapi.com"
PAUSE = 0.2  # ~5 requests/sec, well inside HubSpot's 100/10s private-app ceiling


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True,
                    help="JSON list of {id, name, tier} — the signed-off deletion list")
    ap.add_argument("--tier", action="append", default=None,
                    help="only act on rows whose verdict starts with this (repeatable). "
                         "Default: GREEN only.")
    ap.add_argument("--limit", type=int, help="stop after this many deletions (canary run)")
    ap.add_argument("--confirm-delete", action="store_true",
                    help="actually delete. Without it, nothing is sent.")
    ap.add_argument("--log", type=Path, default=Path("data/deletion-log.jsonl"))
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    import os

    import requests

    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
    if not token:
        print("! HUBSPOT_ACCESS_TOKEN is not set")
        return 2

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"

    tiers = tuple(args.tier or ["GREEN"])
    rows = [r for r in json.loads(args.manifest.read_text())
            if str(r.get("tier", "")).startswith(tiers)]
    if args.limit:
        rows = rows[:args.limit]

    mode = "DELETING" if args.confirm_delete else "DRY RUN — nothing will be sent"
    print(f"{mode}: {len(rows)} workflow(s), tiers {tiers}\n")

    args.log.parent.mkdir(parents=True, exist_ok=True)
    log = args.log.open("a")
    counts = {"deleted": 0, "skipped": 0, "gone": 0, "failed": 0}

    for i, row in enumerate(rows, 1):
        wid, name = str(row["id"]), row["name"]
        head = f"[{i}/{len(rows)}] {name[:56]}  (id {wid})"

        # Re-read the live workflow. The manifest is a claim about the past; this is now.
        try:
            resp = session.get(f"{BASE}/automation/v4/flows/{wid}", timeout=30)
        except requests.RequestException as exc:
            print(f"{head}\n    ! could not read it ({exc}) — skipped")
            counts["failed"] += 1
            continue

        if resp.status_code == 404:
            print(f"{head}\n    · already gone")
            counts["gone"] += 1
            log.write(json.dumps({"at": _stamp(), "id": wid, "name": name,
                                  "outcome": "already-gone"}) + "\n")
            log.flush()
            continue
        if resp.status_code != 200:
            print(f"{head}\n    ! read returned {resp.status_code} — skipped")
            counts["failed"] += 1
            continue

        live = resp.json()
        live_name = (live.get("name") or "").strip()
        # Compare against the state the manifest recorded, not against a fixed
        # expectation of "off". P1-P3 were dormant workflows where being switched on
        # meant something had changed since sign-off; P4 is made entirely of live
        # workflows, where being switched on is the normal case and being switched
        # off is the thing that changed. Either way the rule is the same: if the
        # workflow is not in the state it was signed off in, somebody touched it and
        # it is no longer the thing that was approved.
        expected = row.get("enabled")
        actual = bool(live.get("isEnabled"))
        if expected is None:
            expected = False  # older manifests carry no state; they were all dormant
        if actual != bool(expected):
            was, now = ("on", "off") if expected else ("off", "on")
            print(f"{head}\n    ! was signed off as {was}, is {now} now — skipped")
            counts["skipped"] += 1
            log.write(json.dumps({"at": _stamp(), "id": wid, "name": name,
                                  "outcome": f"skipped-state-changed-{was}-to-{now}"}) + "\n")
            log.flush()
            continue
        if live_name != name.strip():
            print(f"{head}\n    ! name is now {live_name!r} — skipped, this is not the "
                  "workflow that was signed off")
            counts["skipped"] += 1
            log.write(json.dumps({"at": _stamp(), "id": wid, "name": name,
                                  "live_name": live_name,
                                  "outcome": "skipped-name-changed"}) + "\n")
            log.flush()
            continue

        if not args.confirm_delete:
            state = "on" if actual else "off"
            print(f"{head}\n    would delete ({state} as signed off, name matches)")
            continue

        try:
            out = session.delete(f"{BASE}/automation/v4/flows/{wid}", timeout=30)
        except requests.RequestException as exc:
            print(f"{head}\n    ! delete failed ({exc})")
            counts["failed"] += 1
            continue

        ok = out.status_code in (200, 202, 204)
        counts["deleted" if ok else "failed"] += 1
        print(f"{head}\n    {'deleted' if ok else f'! delete returned {out.status_code}'}")
        if not ok:
            print(f"      {out.text[:300]}")
        # HubSpot refuses (400) to delete a workflow other tools still reference. That is a
        # safe refusal, not a partial delete — but the reason only exists in the response
        # body, so keep it: it is the whole explanation for why a row survived.
        log.write(json.dumps({"at": _stamp(), "id": wid, "name": name,
                              "status": out.status_code,
                              "outcome": "deleted" if ok else "failed",
                              "reason": None if ok else out.text[:500]}) + "\n")
        log.flush()
        time.sleep(PAUSE)

    log.close()
    print(f"\n{counts}")
    if args.confirm_delete:
        print(f"log: {args.log}   restore definitions: data/deletion-backup.json")
    return 0 if not counts["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
