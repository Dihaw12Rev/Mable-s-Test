"""Turn a raw portal snapshot into a cross-referenced model of how the portal works.

The core output is a property-usage index: for every property, which workflows read it,
which write it, which forms collect it, and which lists segment on it. That is what
separates a property that matters from one that is merely present.

Workflow definitions are scanned generically rather than against a pinned schema. Keys
known to carry references are read directly, and every remaining string is matched
against the portal's own property names. HubSpot reshapes flow JSON periodically; this
approach degrades to "found fewer references" instead of silently breaking.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from . import links

# Keys whose string values name a CRM property.
PROPERTY_KEYS = {
    "property", "propertyName", "property_name", "targetProperty", "target_property",
    "propertyObjectTypeId", "sourcePropertyName", "hs_property_name",
}
# Keys carrying property names in a *write* position.
WRITE_HINT_KEYS = {"targetProperty", "target_property", "property_name", "propertyName"}

LIST_KEYS = {"listId", "list_id", "listIds", "targetListId", "suppressionListIds", "membershipListId"}
EMAIL_KEYS = {"contentId", "content_id", "emailId", "email_id", "emailContentId"}
FLOW_KEYS = {"flowId", "flow_id", "workflowId", "workflow_id", "targetFlowId"}
FORM_KEYS = {"formId", "form_id", "formGuid", "guid"}
OWNER_KEYS = {"ownerId", "owner_id", "hubspot_owner_id"}

# Best-effort semantics for v4 action type IDs. Anything unrecognised is reported
# verbatim in `unknown_action_types` rather than guessed at.
ACTION_TYPE_NAMES = {
    "0-1": "Delay",
    "0-2": "Set property value",
    "0-3": "Send in-app / internal notification",
    "0-4": "Send marketing email",
    "0-5": "Add to list",
    "0-6": "Remove from list",
    "0-7": "Create task",
    "0-8": "Send internal email notification",
    "0-9": "Webhook",
    "0-10": "Create record",
    "0-11": "Enroll in another workflow",
    "0-13": "Rotate record to owner",
    "0-14": "Send SMS",
    "0-26": "Custom code",
}

BRANCH_TYPES = {"LIST_BRANCH", "STATIC_BRANCH", "AB_TEST_BRANCH", "BRANCH"}

SYSTEM_RULES = [
    ("Lifecycle & Stage Management", r"lifecycle|mql|sql|stage|sqo|funnel|handoff|hand-off"),
    ("Lead Routing & Assignment", r"rout|assign|owner|territor|rotat|round.?robin|distribut"),
    ("Lead Scoring & Qualification", r"scor|grade|fit|qualif|icp|tier|rating"),
    ("Deliverability & Suppression", r"bounce|unsub|suppress|opt.?out|deliverab|spam|gdpr|ccpa|consent"),
    ("Nurture & Marketing Campaigns", r"nurture|drip|campaign|newsletter|webinar|promo|re.?engag|welcome|onboard.*email"),
    ("Data Hygiene & Normalization", r"clean|hygien|normal|standard|dedup|format|enrich|backfill|fix|correct"),
    ("Internal Notifications & Alerts", r"notif|alert|slack|email.*team|internal|escalat"),
    ("Sales & Deal Automation", r"deal|pipeline|quote|contract|renewal|churn|upsell|opportunit"),
    ("Customer Onboarding & Success", r"onboard|activation|adoption|csm|success|nps|survey"),
    ("Integrations & Sync", r"sync|salesforce|sfdc|integrat|zapier|api|webhook|import"),
]


# --------------------------------------------------------------------- generic scan


def walk(node: Any, path: str = "") -> Iterable[tuple[str, str, Any]]:
    """Yield (path, key, value) for every key/value pair in a nested structure."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            yield here, key, value
            yield from walk(value, here)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            here = f"{path}[{i}]"
            yield from walk(item, here)


def _as_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [str(value)]
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            out.extend(_as_strings(v))
        return out
    return []


class Analysis:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.portal_id = str(
            (snapshot.get("account") or {}).get("portalId")
            or (snapshot.get("account") or {}).get("portal_id")
            or "PORTAL_ID"
        )
        self.properties = snapshot.get("properties", {})
        self.known_props: dict[str, set[str]] = {
            obj: {p["name"] for p in props} for obj, props in self.properties.items()
        }
        self.all_prop_names: set[str] = set()
        for names in self.known_props.values():
            self.all_prop_names |= names

        self.coverage = _coverage(snapshot)
        # Every reference source must be readable before absence of a reference
        # can be reported as absence of use.
        self.usage_complete = all(self.coverage.values())

        self.unknown_action_types: Counter[str] = Counter()
        self.usage: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: {
                "written_by_workflows": set(),
                "read_by_workflows": set(),
                "collected_by_forms": set(),
                "segmented_by_lists": set(),
            }
        )

    # ------------------------------------------------------------------ workflows

    def analyze_workflows(self) -> list[dict[str, Any]]:
        out = []
        for flow in self.snapshot.get("workflows", []):
            out.append(self._analyze_flow(flow))
        self.workflows = out
        return out

    def _analyze_flow(self, flow: dict[str, Any]) -> dict[str, Any]:
        fid = str(flow.get("id"))
        enrollment = flow.get("enrollmentCriteria") or {}
        actions = flow.get("actions") or []

        read, written = self._scan_properties(flow, enrollment, actions)
        refs = self._scan_refs(flow)
        action_summary, branch_count = self._summarize_actions(actions)

        record = {
            "id": fid,
            "name": flow.get("name") or "(unnamed)",
            "enabled": bool(flow.get("isEnabled")),
            "type": flow.get("type"),
            "object_type": flow.get("objectTypeId"),
            "created_at": flow.get("createdAt"),
            "updated_at": flow.get("updatedAt"),
            "revision_id": flow.get("revisionId"),
            "definition_available": flow.get("_definition_available", False),
            "link": links.workflow(self.portal_id, fid),
            "enrollment_type": enrollment.get("type"),
            "re_enrollment": bool(enrollment.get("shouldReEnroll")),
            "unenroll_on_criteria_winback": bool(flow.get("unEnrollObjectsOnCriteriaWinBack")),
            "action_count": len(actions),
            "branch_count": branch_count,
            "actions": action_summary,
            "properties_read": sorted(read),
            "properties_written": sorted(written),
            "lists_referenced": sorted(refs["lists"]),
            "emails_referenced": sorted(refs["emails"]),
            "workflows_triggered": sorted(refs["flows"]),
            "forms_referenced": sorted(refs["forms"]),
            "suppression_lists": [str(x) for x in (flow.get("suppressionListIds") or [])],
        }
        record["description"] = self._describe(record)

        for name in read:
            self.usage[name]["read_by_workflows"].add(fid)
        for name in written:
            self.usage[name]["written_by_workflows"].add(fid)
        return record

    def _scan_properties(
        self, flow: dict[str, Any], enrollment: dict[str, Any], actions: list[Any]
    ) -> tuple[set[str], set[str]]:
        """Split property references into read (criteria/branches) and written (actions)."""
        read: set[str] = set()
        written: set[str] = set()

        for _, key, value in walk(enrollment):
            if key in PROPERTY_KEYS:
                read.update(v for v in _as_strings(value) if v in self.all_prop_names)

        for action in actions:
            is_branch = str(action.get("type", "")).upper() in BRANCH_TYPES
            target = read if is_branch else written
            for _, key, value in walk(action):
                if key not in PROPERTY_KEYS:
                    continue
                names = [v for v in _as_strings(value) if v in self.all_prop_names]
                if key in WRITE_HINT_KEYS and not is_branch:
                    written.update(names)
                else:
                    target.update(names)

        # Fallback sweep: any bare string in the definition that exactly matches a real
        # property name. Catches schema shapes the key list above does not cover.
        seen = read | written
        for _, key, value in walk(flow):
            if key in {"name", "label", "description"}:
                continue
            for candidate in _as_strings(value):
                if candidate in self.all_prop_names and candidate not in seen:
                    read.add(candidate)

        return read, written

    def _scan_refs(self, flow: dict[str, Any]) -> dict[str, set[str]]:
        refs = {"lists": set(), "emails": set(), "flows": set(), "forms": set(), "owners": set()}
        own_id = str(flow.get("id"))
        for _, key, value in walk(flow):
            if key in LIST_KEYS:
                refs["lists"].update(_as_strings(value))
            elif key in EMAIL_KEYS:
                refs["emails"].update(_as_strings(value))
            elif key in FLOW_KEYS:
                refs["flows"].update(v for v in _as_strings(value) if v != own_id)
            elif key in FORM_KEYS:
                refs["forms"].update(_as_strings(value))
            elif key in OWNER_KEYS:
                refs["owners"].update(_as_strings(value))
        return refs

    def _summarize_actions(self, actions: list[Any]) -> tuple[list[dict[str, Any]], int]:
        summary: list[dict[str, Any]] = []
        branches = 0
        for action in actions:
            a_type = str(action.get("type", ""))
            type_id = str(action.get("actionTypeId", ""))
            if a_type.upper() in BRANCH_TYPES:
                branches += 1
                label = "Branch"
            elif type_id in ACTION_TYPE_NAMES:
                label = ACTION_TYPE_NAMES[type_id]
            else:
                label = f"{a_type or 'Action'} ({type_id})" if type_id else (a_type or "Action")
                if type_id:
                    self.unknown_action_types[type_id] += 1
            summary.append({"id": action.get("actionId"), "label": label, "type_id": type_id})
        return summary, branches

    def _describe(self, r: dict[str, Any]) -> str:
        """A plain-language sentence or two about what this workflow does."""
        if not r["definition_available"]:
            return (
                "Full definition could not be read from the API (the token or plan tier "
                "does not expose it). Name, status, and timestamps only."
            )

        obj = _object_label(r["object_type"])
        state = "Active" if r["enabled"] else "Turned off"
        parts = [f"{state} {obj} workflow."]

        if r["properties_read"]:
            shown = ", ".join(f"`{p}`" for p in r["properties_read"][:6])
            more = f" (+{len(r['properties_read']) - 6} more)" if len(r["properties_read"]) > 6 else ""
            parts.append(f"Enrolls and branches on {shown}{more}.")
        elif r["enrollment_type"]:
            parts.append(f"Enrollment type: {r['enrollment_type']}.")

        if r["properties_written"]:
            shown = ", ".join(f"`{p}`" for p in r["properties_written"][:6])
            more = f" (+{len(r['properties_written']) - 6} more)" if len(r["properties_written"]) > 6 else ""
            parts.append(f"Writes {shown}{more}.")

        counts = Counter(a["label"] for a in r["actions"])
        if counts:
            steps = ", ".join(f"{n}× {label}" for label, n in counts.most_common(6))
            parts.append(f"{r['action_count']} steps: {steps}.")

        if r["workflows_triggered"]:
            parts.append(f"Hands off to {len(r['workflows_triggered'])} other workflow(s).")
        if r["suppression_lists"]:
            parts.append(f"{len(r['suppression_lists'])} suppression list(s) applied.")
        if r["re_enrollment"]:
            parts.append("Re-enrollment is on.")
        return " ".join(parts)

    # ---------------------------------------------------------------------- forms

    def analyze_forms(self) -> list[dict[str, Any]]:
        out = []
        for form in self.snapshot.get("forms", []):
            fid = str(form.get("id") or form.get("guid"))
            fields: set[str] = set()
            for group in form.get("fieldGroups", []) or []:
                for field in group.get("fields", []) or []:
                    name = field.get("name")
                    if name:
                        fields.add(name)
            if not fields:
                for _, key, value in walk(form):
                    if key == "name":
                        fields.update(v for v in _as_strings(value) if v in self.all_prop_names)

            for name in fields:
                self.usage[name]["collected_by_forms"].add(fid)

            out.append({
                "id": fid,
                "name": form.get("name") or "(unnamed)",
                "type": form.get("formType"),
                "archived": bool(form.get("archived")),
                "created_at": form.get("createdAt"),
                "updated_at": form.get("updatedAt"),
                "link": links.form(self.portal_id, fid),
                "fields": sorted(fields),
                "field_count": len(fields),
                "description": (
                    f"{form.get('formType') or 'Form'} collecting {len(fields)} field(s)"
                    + (f": {', '.join(sorted(fields)[:8])}." if fields else ".")
                ),
            })
        self.forms = out
        return out

    # ---------------------------------------------------------------------- lists

    def analyze_lists(self) -> list[dict[str, Any]]:
        out = []
        for lst in self.snapshot.get("lists", []):
            lid = str(lst.get("listId") or lst.get("id"))
            props: set[str] = set()
            for _, key, value in walk(lst):
                if key in PROPERTY_KEYS:
                    props.update(v for v in _as_strings(value) if v in self.all_prop_names)
            for name in props:
                self.usage[name]["segmented_by_lists"].add(lid)

            out.append({
                "id": lid,
                "name": lst.get("name") or "(unnamed)",
                "processing_type": lst.get("processingType"),
                "object_type": lst.get("objectTypeId"),
                "size": lst.get("additionalProperties", {}).get("hs_list_size")
                        or lst.get("size"),
                "created_at": lst.get("createdAt"),
                "updated_at": lst.get("updatedAt"),
                "link": links.hs_list(self.portal_id, lid),
                "properties": sorted(props),
                "description": (
                    f"{(lst.get('processingType') or 'LIST').title()} list"
                    + (f" segmenting on {', '.join(sorted(props)[:6])}." if props else ".")
                ),
            })
        self.lists = out
        return out

    # ----------------------------------------------------------------- properties

    def analyze_properties(self) -> list[dict[str, Any]]:
        """Must run after workflows, forms, and lists so the usage index is populated."""
        out = []
        for obj_type, props in self.properties.items():
            for p in props:
                name = p["name"]
                u = self.usage.get(name)
                wf_write = sorted(u["written_by_workflows"]) if u else []
                wf_read = sorted(u["read_by_workflows"]) if u else []
                forms_ = sorted(u["collected_by_forms"]) if u else []
                lists_ = sorted(u["segmented_by_lists"]) if u else []
                score = (
                    3 * len(wf_write) + 2 * len(wf_read) + 2 * len(forms_) + 2 * len(lists_)
                )
                out.append({
                    "name": name,
                    "object_type": obj_type,
                    "label": p.get("label"),
                    "description": p.get("description") or "",
                    "type": p.get("type"),
                    "field_type": p.get("fieldType"),
                    "group": p.get("groupName"),
                    "hubspot_defined": bool(p.get("hubspotDefined")),
                    "calculated": bool(p.get("calculated")),
                    "read_only": bool(p.get("modificationMetadata", {}).get("readOnlyValue")),
                    "archived": bool(p.get("archived")),
                    "option_count": len(p.get("options") or []),
                    "created_at": p.get("createdAt"),
                    "updated_at": p.get("updatedAt"),
                    "link": links.prop(self.portal_id, obj_type, name),
                    "written_by_workflows": wf_write,
                    "read_by_workflows": wf_read,
                    "collected_by_forms": forms_,
                    "segmented_by_lists": lists_,
                    "usage_score": score,
                    # "Unused" is only knowable when every reference source was readable.
                    # With workflows or forms missing, a zero score means "unknown".
                    "unused": (
                        score == 0
                        and not p.get("hubspotDefined")
                        and self.usage_complete
                    ),
                    "usage_known": self.usage_complete,
                })
        out.sort(key=lambda r: (-r["usage_score"], r["object_type"], r["name"]))
        self.property_records = out
        return out

    # -------------------------------------------------------------------- systems

    def group_systems(self) -> dict[str, list[dict[str, Any]]]:
        systems: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for wf in self.workflows:
            systems[_classify(wf["name"])].append(wf)
        self.systems = dict(sorted(systems.items(), key=lambda kv: -len(kv[1])))
        return self.systems

    def dependency_clusters(self) -> list[list[str]]:
        """Connected components over workflows that share a written/read property."""
        by_prop: dict[str, set[str]] = defaultdict(set)
        for wf in self.workflows:
            for name in wf["properties_written"] + wf["properties_read"]:
                by_prop[name].add(wf["id"])
        for wf in self.workflows:
            for target in wf["workflows_triggered"]:
                by_prop[f"_handoff_{wf['id']}"].update({wf["id"], target})

        parent: dict[str, str] = {}

        def find(x: str) -> str:
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for wf in self.workflows:
            find(wf["id"])
        for members in by_prop.values():
            members = list(members)
            for other in members[1:]:
                union(members[0], other)

        groups: dict[str, list[str]] = defaultdict(list)
        for wf in self.workflows:
            groups[find(wf["id"])].append(wf["id"])
        clusters = sorted(groups.values(), key=len, reverse=True)
        self.clusters = [c for c in clusters if len(c) > 1]
        return self.clusters


# Endpoints whose absence makes the property usage index incomplete. A property can
# only be called unreferenced if every one of these was read successfully.
USAGE_SOURCES = {
    "workflows": "automation/v4/flows",
    "forms": "marketing/v3/forms",
    "lists": "crm/v3/lists",
}


def _coverage(snapshot: dict[str, Any]) -> dict[str, bool]:
    missed = {s.get("endpoint", "") for s in snapshot.get("skipped", [])}
    return {
        source: not any(path in endpoint for endpoint in missed)
        for source, path in USAGE_SOURCES.items()
    }


def _classify(name: str) -> str:
    lowered = (name or "").lower()
    for label, pattern in SYSTEM_RULES:
        if re.search(pattern, lowered):
            return label
    return "Uncategorized"


def _object_label(object_type_id: Any) -> str:
    mapping = {
        "0-1": "contact", "0-2": "company", "0-3": "deal",
        "0-5": "ticket", "0-8": "line item", "0-14": "quote",
    }
    return mapping.get(str(object_type_id), "record")


def run(snapshot: dict[str, Any]) -> dict[str, Any]:
    a = Analysis(snapshot)
    workflows = a.analyze_workflows()
    forms = a.analyze_forms()
    lists_ = a.analyze_lists()
    properties = a.analyze_properties()
    systems = a.group_systems()
    clusters = a.dependency_clusters()

    return {
        "portal_id": a.portal_id,
        "account": snapshot.get("account", {}),
        "extracted_at": snapshot.get("extracted_at"),
        "workflows": workflows,
        "properties": properties,
        "forms": forms,
        "lists": lists_,
        "marketing_emails": _simple_assets(
            snapshot.get("marketing_emails", []), a.portal_id, links.marketing_email, "email"
        ),
        "landing_pages": _simple_assets(
            snapshot.get("landing_pages", []), a.portal_id, links.page, "landing page"
        ),
        "site_pages": _simple_assets(
            snapshot.get("site_pages", []), a.portal_id, links.page, "site page"
        ),
        "blog_posts": _simple_assets(
            snapshot.get("blog_posts", []), a.portal_id, links.blog_post, "blog post"
        ),
        "owners": snapshot.get("owners", []),
        "pipelines": snapshot.get("pipelines", {}),
        "systems": {k: [w["id"] for w in v] for k, v in systems.items()},
        "clusters": clusters,
        "skipped": snapshot.get("skipped", []),
        "coverage": a.coverage,
        "usage_complete": a.usage_complete,
        "unknown_action_types": dict(a.unknown_action_types),
    }


def _simple_assets(items, portal_id, link_fn, kind) -> list[dict[str, Any]]:
    out = []
    for item in items:
        aid = str(item.get("id"))
        out.append({
            "id": aid,
            "name": item.get("name") or item.get("subject") or "(unnamed)",
            "subject": item.get("subject"),
            "slug": item.get("slug"),
            "url": item.get("url") or item.get("absoluteUrl"),
            "state": item.get("state") or item.get("currentState"),
            "archived": bool(item.get("archived")),
            "created_at": item.get("createdAt") or item.get("created"),
            "updated_at": item.get("updatedAt") or item.get("updated"),
            "publish_date": item.get("publishDate"),
            "link": link_fn(portal_id, aid),
            "kind": kind,
        })
    return out
