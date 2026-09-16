"""Pull a full, read-only snapshot of a HubSpot portal to disk.

Each asset family is fetched independently and failures are isolated: a portal without
Marketing Hub still produces a complete workflow and property inventory, with the
unreachable endpoints recorded so the report can state what was not covered.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import Client, ScopeError

# CRM object types with properties worth inventorying. Custom objects are discovered
# at runtime and appended.
STANDARD_OBJECTS = [
    "contacts",
    "companies",
    "deals",
    "tickets",
    "products",
    "line_items",
    "quotes",
]

PIPELINE_OBJECTS = ["deals", "tickets"]


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_all(client: Client, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, Any] = {"extracted_at": _stamp()}

    print("Extracting HubSpot portal snapshot...")
    snapshot["account"] = _account(client)
    snapshot["owners"] = _owners(client)
    snapshot["schemas"] = _schemas(client)
    snapshot["properties"] = _properties(client, snapshot["schemas"])
    snapshot["property_groups"] = _property_groups(client, snapshot["properties"].keys())
    snapshot["workflows"] = _workflows(client)
    snapshot["lists"] = _lists(client)
    snapshot["forms"] = _forms(client)
    snapshot["marketing_emails"] = _marketing_emails(client)
    snapshot["landing_pages"] = _pages(client, "landing-pages")
    snapshot["site_pages"] = _pages(client, "site-pages")
    snapshot["blog_posts"] = _blog_posts(client)
    snapshot["pipelines"] = _pipelines(client)
    snapshot["skipped"] = [asdict(s) for s in client.skipped]

    path = out_dir / "snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, default=str))
    print(f"\nSnapshot written to {path}")
    _summarize(snapshot)
    return snapshot


# --------------------------------------------------------------------------- account


def _account(client: Client) -> dict[str, Any]:
    print("- account details")
    try:
        details = client.get("/account-info/v3/details")
    except ScopeError as exc:
        print(f"  ! account details unavailable ({exc})")
        return {}
    try:
        details["api_usage"] = client.get("/account-info/v3/api-usage/daily")
    except ScopeError:
        pass
    return details


def _owners(client: Client) -> list[dict[str, Any]]:
    print("- owners")
    active = client.collect("owners", "/crm/v3/owners", {"archived": "false"})
    archived = client.collect("owners (archived)", "/crm/v3/owners", {"archived": "true"})
    for o in archived:
        o["_archived"] = True
    return active + archived


# ------------------------------------------------------------------------ properties


def _schemas(client: Client) -> list[dict[str, Any]]:
    print("- custom object schemas")
    try:
        return client.get("/crm/v3/schemas").get("results", [])
    except ScopeError as exc:
        print(f"  ! schemas unavailable ({exc})")
        return []


def _properties(client: Client, schemas: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    print("- properties")
    object_types = list(STANDARD_OBJECTS)
    object_types += [s["fullyQualifiedName"] for s in schemas if s.get("fullyQualifiedName")]

    out: dict[str, list[dict[str, Any]]] = {}
    for obj in object_types:
        try:
            props = client.get(f"/crm/v3/properties/{obj}").get("results", [])
        except ScopeError:
            continue
        out[obj] = props
        print(f"  · {obj}: {len(props)} properties")
    return out


def _property_groups(client: Client, object_types) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for obj in object_types:
        try:
            out[obj] = client.get(f"/crm/v3/properties/{obj}/groups").get("results", [])
        except ScopeError:
            continue
    return out


# ------------------------------------------------------------------------- workflows


def _workflows(client: Client) -> list[dict[str, Any]]:
    print("- workflows (v4 Automation API)")
    summaries = client.collect("workflows", "/automation/v4/flows")
    if not summaries:
        return []

    ids = [str(f["id"]) for f in summaries if f.get("id")]
    full: dict[str, dict[str, Any]] = {}

    # Batch read is far cheaper than per-flow GETs, but the endpoint is fussy about
    # payload shape and not enabled on every portal. Try both documented shapes,
    # then fall back to individual GETs. Any failure here is an optimisation lost,
    # never a failed run, so the fallback catches transport errors too.
    for chunk in _chunks(ids, 100):
        got = False
        for payload in ({"inputs": chunk}, {"inputs": [{"flowId": f} for f in chunk]}):
            try:
                resp = client.post("/automation/v4/flows/batch/read", payload)
            except Exception:
                continue
            results = resp.get("results") or []
            if results:
                for flow in results:
                    full[str(flow.get("id"))] = flow
                got = True
                break
        if got:
            continue
        for fid in chunk:
            try:
                full[fid] = client.get(f"/automation/v4/flows/{fid}")
            except (ScopeError, Exception):
                continue

    merged = []
    for summary in summaries:
        fid = str(summary.get("id"))
        record = dict(summary)
        record.update(full.get(fid, {}))
        record["_definition_available"] = fid in full
        merged.append(record)

    _attach_enrollment(client, merged)
    print(f"  · {len(merged)} workflows ({sum(1 for m in merged if m['_definition_available'])} with full definitions)")
    return merged


# Legacy IDs are embedded in the v4 uuid, e.g. hybrid-execution-wf-7023659.
_LEGACY_ID = re.compile(r"(\d+)$")


def _attach_enrollment(client: Client, flows: list[dict[str, Any]]) -> None:
    """Add lifetime and current enrolment counts from the legacy workflows API.

    The v4 Automation API returns a workflow's logic but no measure of whether it
    has ever run. The legacy list endpoint still reports contactCounts, which is
    the only place enrolment is exposed at all — there is no per-workflow
    performance route, and no endpoint dates an enrolment. Counts are matched to v4
    flows by the legacy id inside the uuid, falling back to an unambiguous name
    match; anything still unmatched is left unmeasured rather than guessed at.
    """
    try:
        legacy = client.get("/automation/v3/workflows").get("workflows", [])
    except (ScopeError, Exception) as exc:
        print(f"  ! enrolment counts unavailable ({str(exc)[:90]})")
        return
    if not legacy:
        return

    by_id = {str(w["id"]): w for w in legacy}
    by_name: dict[str, list[dict[str, Any]]] = {}
    for w in legacy:
        by_name.setdefault((w.get("name") or "").strip().lower(), []).append(w)

    matched = 0
    for flow in flows:
        found = None
        hit = _LEGACY_ID.search(str(flow.get("uuid") or ""))
        if hit and hit.group(1) in by_id:
            found = by_id[hit.group(1)]
        else:
            same_name = by_name.get((flow.get("name") or "").strip().lower(), [])
            if len(same_name) == 1:
                found = same_name[0]
        if not found:
            continue
        counts = found.get("contactCounts") or {}
        flow["_enrolled_total"] = counts.get("enrolled")
        flow["_enrolled_active"] = counts.get("active")
        flow["_legacy_id"] = str(found.get("id"))
        matched += 1
    never = sum(1 for f in flows if f.get("_enrolled_total") == 0)
    print(f"  · enrolment counts for {matched} of {len(flows)} ({never} never enrolled anyone)")


# ----------------------------------------------------------------------------- lists


def _lists(client: Client) -> list[dict[str, Any]]:
    print("- lists")
    results: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            resp = client.post(
                "/crm/v3/lists/search",
                {"query": "", "count": 100, "offset": offset, "processingTypes": []},
            )
        except ScopeError as exc:
            client.skipped.append(_skip("/crm/v3/lists/search", exc))
            print(f"  ! lists unavailable ({exc})")
            break
        batch = resp.get("lists", []) or resp.get("results", [])
        results.extend(batch)
        total = resp.get("total", 0)
        offset += len(batch)
        if not batch or offset >= total:
            break

    # The search payload omits filter definitions; fetch each list to get its criteria.
    for lst in results:
        list_id = lst.get("listId") or lst.get("id")
        if not list_id:
            continue
        try:
            detail = client.get(f"/crm/v3/lists/{list_id}", {"includeFilters": "true"})
            lst.update(detail.get("list", detail))
        except ScopeError:
            continue

    print(f"  · {len(results)} lists")
    return results


# ----------------------------------------------------------------- marketing assets


def _forms(client: Client) -> list[dict[str, Any]]:
    print("- forms")
    forms = client.collect("forms", "/marketing/v3/forms")
    print(f"  · {len(forms)} forms")
    return forms


def _marketing_emails(client: Client) -> list[dict[str, Any]]:
    print("- marketing emails")
    emails = client.collect("marketing emails", "/marketing/v3/emails")
    print(f"  · {len(emails)} marketing emails")
    return emails


def _pages(client: Client, kind: str) -> list[dict[str, Any]]:
    print(f"- {kind.replace('-', ' ')}")
    pages = client.collect(kind, f"/cms/v3/pages/{kind}")
    print(f"  · {len(pages)} {kind}")
    return pages


def _blog_posts(client: Client) -> list[dict[str, Any]]:
    print("- blog posts")
    posts = client.collect("blog posts", "/cms/v3/blogs/posts")
    print(f"  · {len(posts)} blog posts")
    return posts


def _pipelines(client: Client) -> dict[str, list[dict[str, Any]]]:
    print("- pipelines")
    out: dict[str, list[dict[str, Any]]] = {}
    for obj in PIPELINE_OBJECTS:
        try:
            out[obj] = client.get(f"/crm/v3/pipelines/{obj}").get("results", [])
        except ScopeError:
            continue
    return out


# ----------------------------------------------------------------------------- utils


def _chunks(items: list[str], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _skip(endpoint: str, exc: Exception):
    from .client import Skipped

    head = str(exc).split(" ", 1)[0]
    return Skipped(endpoint=endpoint, status=int(head) if head.isdigit() else None, reason=str(exc))


def _summarize(snapshot: dict[str, Any]) -> None:
    prop_total = sum(len(v) for v in snapshot.get("properties", {}).values())
    print(
        f"\n  workflows={len(snapshot.get('workflows', []))} "
        f"properties={prop_total} "
        f"lists={len(snapshot.get('lists', []))} "
        f"forms={len(snapshot.get('forms', []))} "
        f"emails={len(snapshot.get('marketing_emails', []))} "
        f"landing_pages={len(snapshot.get('landing_pages', []))} "
        f"site_pages={len(snapshot.get('site_pages', []))}"
    )
    if snapshot.get("skipped"):
        print(f"  {len(snapshot['skipped'])} endpoint(s) unavailable - see report appendix")
        wanted = sorted({n for s in snapshot["skipped"] for n in (s.get("required_scopes") or [])})
        if wanted:
            print("  add these scopes to the private app and re-run: " + ", ".join(wanted))
