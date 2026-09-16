"""Measure how properties are actually used on records, not just how they are wired.

The audit proper reads the account's shape: which workflows, forms and lists
reference a property. That misses the field a person fills in by hand on every
record, which looks identical to a dead one. This module closes that gap with two
measurements that need record access:

    fill rate     how many records carry any value
    last written  the most recent write seen, and what made it

Neither can be had in bulk from HubSpot, so both are sampled deliberately: fill
rate from search totals (exact), last-written from the most recently modified
records (a floor, never a ceiling — a field may have been written more recently on
a record outside the sample).

Note on workflow attribution: history records automation writes as
`enrollmentId:...;actionExecutionIndex:N`, which names the enrolment, not the
workflow, and no endpoint resolves one to the other. So a write can be reported as
"automation did this" but never as "workflow X did this".
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from .client import Client, ScopeError

# How the source of a write reads to someone who does not know HubSpot's vocabulary.
SOURCE_LABELS = {
    "AUTOMATION_PLATFORM": "Automation",
    "FORM": "Form submission",
    "CRM_UI": "Someone typing",
    "CRM_UI_BULK_ACTION": "Bulk edit in HubSpot",
    "BATCH_UPDATE": "Bulk update",
    "IMPORT": "Import",
    "INTEGRATIONS_SYNC": "Integration sync",
    "INTEGRATION": "Integration",
    "EXTENSION": "Connected app",
    "API": "API",
    "EMAIL_INTEGRATION": "Email integration",
    "SALESFORCE": "Salesforce sync",
    "CONTACTS": "HubSpot (contact activity)",
    "CONTACTS_WEB": "Website activity",
    "COMPANIES": "HubSpot (company activity)",
    "DEALS": "HubSpot (deal activity)",
    "ANALYTICS": "Analytics",
    "MIGRATION": "Migration",
    "TASK": "Task",
    "ASSISTS": "HubSpot assist",
}

# Properties per history request. HubSpot caps the propertiesWithHistory list, and
# a wide list against many records returns a very large payload.
HISTORY_CHUNK = 12
# Hard limit from HubSpot: "the maximum number of inputs supported in a batch
# request for property histories is 50". Larger batches 400 outright.
HISTORY_BATCH = 50
SAMPLE_SIZE = 200

# The last-modified property differs by object; contacts predate the hs_ prefix.
MODIFIED_PROPERTY = {"contacts": "lastmodifieddate"}


def label_source(source_type: str | None) -> str:
    if not source_type:
        return "Unknown"
    return SOURCE_LABELS.get(source_type, source_type.replace("_", " ").title())


def _iso(value: Any) -> str:
    if not value:
        return ""
    text = str(value)
    if text.isdigit():  # epoch millis
        return datetime.fromtimestamp(int(text) / 1000, timezone.utc).date().isoformat()
    return text[:10]


def total_records(client: Client, object_type: str) -> int | None:
    """How many records the object holds, for the fill-rate denominator."""
    try:
        return client.post(f"/crm/v3/objects/{object_type}/search",
                           {"filterGroups": [], "limit": 1}).get("total")
    except (ScopeError, Exception):
        return None


def fill_rate(client: Client, object_type: str, prop: str) -> int | None:
    """How many records carry any value for this property. Exact, one call."""
    body = {
        "filterGroups": [{"filters": [{"propertyName": prop, "operator": "HAS_PROPERTY"}]}],
        "limit": 1,
    }
    try:
        return client.post(f"/crm/v3/objects/{object_type}/search", body).get("total")
    except Exception:
        return None


def _recent_ids(client: Client, object_type: str, limit: int) -> list[str]:
    """Ids of the most recently modified records.

    Sampling the freshest records is the right bias: the question is whether a
    field is still being written, and if it is, it will show up here first.
    """
    ids: list[str] = []
    after = 0
    while len(ids) < limit:
        body = {
            "filterGroups": [],
            "sorts": [{"propertyName": MODIFIED_PROPERTY.get(object_type, "hs_lastmodifieddate"),
                       "direction": "DESCENDING"}],
            "limit": min(100, limit - len(ids)),
            "after": after,
        }
        try:
            page = client.post(f"/crm/v3/objects/{object_type}/search", body)
        except Exception as exc:
            print(f"    ! id search failed: {type(exc).__name__}: {str(exc)[:200]}")
            break
        results = page.get("results", [])
        if not results:
            break
        ids.extend(r["id"] for r in results)
        after += len(results)
        if not page.get("paging"):
            break
    return ids


def last_written(
    client: Client, object_type: str, props: list[str], record_ids: list[str]
) -> dict[str, dict[str, Any]]:
    """Newest write seen per property across the sampled records, with its source."""
    found: dict[str, dict[str, Any]] = {}
    for chunk in _chunks(props, HISTORY_CHUNK):
        for batch in _chunks(record_ids, HISTORY_BATCH):
            body = {
                "inputs": [{"id": rid} for rid in batch],
                "propertiesWithHistory": chunk,
                "properties": ["hs_object_id"],
            }
            try:
                resp = client.post(f"/crm/v3/objects/{object_type}/batch/read", body)
            except Exception as exc:
                print(f"    ! history batch failed: {type(exc).__name__}: {str(exc)[:200]}")
                continue
            for rec in resp.get("results", []):
                for prop, entries in (rec.get("propertiesWithHistory") or {}).items():
                    for entry in entries or []:
                        stamp = _iso(entry.get("timestamp"))
                        if not stamp:
                            continue
                        current = found.get(prop)
                        if current is None or stamp > current["last_written"]:
                            found[prop] = {
                                "last_written": stamp,
                                "source": label_source(entry.get("sourceType")),
                                "source_raw": entry.get("sourceType"),
                            }
                        if current:
                            current.setdefault("sources", Counter())
                        found[prop].setdefault("sources", Counter())[
                            label_source(entry.get("sourceType"))
                        ] += 1
    return found


def measure(client: Client, analysis: dict[str, Any], objects: Iterable[str] | None = None,
            sample: int = SAMPLE_SIZE) -> dict[str, Any]:
    """Fill rate and last-written for every property on the requested objects."""
    by_object: dict[str, list[dict[str, Any]]] = {}
    for prop in analysis["properties"]:
        by_object.setdefault(prop["object_type"], []).append(prop)

    wanted = list(objects) if objects else [o for o in by_object if not o.startswith("p")]
    out: dict[str, Any] = {"measured_at": datetime.now(timezone.utc).isoformat(),
                           "sample_size": sample, "objects": {}, "properties": {}}

    for obj in wanted:
        props = by_object.get(obj) or []
        if not props:
            continue
        total = total_records(client, obj)
        print(f"- {obj}: {len(props)} properties over {total if total is not None else '?'} records")
        out["objects"][obj] = {"total_records": total}

        ids = _recent_ids(client, obj, sample)
        print(f"    sampling history from {len(ids)} most recently modified records")
        history = last_written(client, obj, [p["name"] for p in props], ids)

        for i, prop in enumerate(props, 1):
            filled = fill_rate(client, obj, prop["name"])
            hist = history.get(prop["name"]) or {}
            sources = hist.get("sources")
            out["properties"][prop["key"]] = {
                "filled": filled,
                "total": total,
                "fill_pct": (round(filled / total * 100, 1)
                             if filled is not None and total else None),
                "last_written": hist.get("last_written") or "",
                "last_written_by": hist.get("source") or "",
                "written_by": [s for s, _ in sources.most_common(4)] if sources else [],
                "history_seen": bool(hist),
            }
            if i % 200 == 0:
                print(f"    fill rate {i}/{len(props)}")
    return out


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
