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
# Native action type IDs, confirmed against real v4 payloads by their field shapes
# (e.g. 0-5 carries property_name/value, so it is the set-property action).
ACTION_TYPE_NAMES = {
    # Native actions, confirmed against real v4 payloads by their field shapes.
    "0-1": "Delay",
    "0-2": "Delay until event",
    "0-3": "Create task",
    "0-4": "Send marketing email",
    "0-5": "Set property value",
    "0-8": "Send internal notification",
    "0-9": "Webhook",
    "0-11": "Rotate record to owner",
    "0-13": "Add to static list",
    "0-14": "Create record",
    "0-15": "Enrol in another workflow",
    "0-23": "Send internal email",
    "0-25": "Copy property value",
    "0-28": "Delay",
    "0-29": "Wait for event",
    "0-31": "Set marketing contact status",
    "0-35": "Delay until date or time",
    "0-43347357": "Set email subscription status",
    "0-46510720": "Enrol in sequence",
    "0-63189541": "Create or associate records",
    "0-63809083": "Add or remove from list",
    "0-63863438": "Add or remove from list",
    "0-169425243": "Create note",
    "0-261589386": "Increase or decrease a number property",
    # App extension actions, identified by the app-specific fields they carry.
    "1-179507819": "Send Slack message",
    "1-1633220": "Create Jira issue",
    "1-24662337": "Create ClickUp task",
    "1-2796901": "Add a Google Sheets row",
    "1-9488285": "Find or update a Google Sheets row",
    "1-38840228": "Copy a property (app action)",
    "1-38840229": "Copy a property (app action)",
    "1-1567": "Trigger an external app",
    "1-1612850": "Apply an app template",
    "1-75176113": "Look up a phone number",
}

# Field keys that identify an action when its type ID is unrecognised. Ordered:
# the first match wins, so the more specific shapes come first.
ACTION_FIELD_HINTS = [
    ({"source_code", "sourceCode"}, "Custom code"),
    ({"webhook_url", "url"}, "Webhook"),
    ({"property_name", "propertyName"}, "Set property value"),
    ({"content_id", "contentId"}, "Send marketing email"),
    ({"task_type", "taskType"}, "Create task"),
    ({"listId", "list_id"}, "List membership"),
    ({"delta", "time_unit"}, "Delay"),
    ({"subject", "body"}, "Send notification"),
]

BRANCH_TYPES = {"LIST_BRANCH", "STATIC_BRANCH", "AB_TEST_BRANCH", "BRANCH"}

# HubSpot object type IDs -> CRM object name, used to resolve which object a
# property reference belongs to. `lifecyclestage` on a contact workflow is
# contacts.lifecyclestage, not the identically named company property.
OBJECT_BY_TYPE_ID = {
    "0-1": "contacts", "0-2": "companies", "0-3": "deals", "0-5": "tickets",
    "0-7": "products", "0-8": "line_items", "0-14": "quotes", "0-27": "tasks",
    "0-48": "calls", "0-49": "emails", "0-47": "meetings", "0-4": "notes",
}

# Names HubSpot generates for a workflow nobody titled. Classifying these by name
# is meaningless, so behaviour decides instead.
AUTO_NAME = re.compile(r"^\s*(unnamed workflow|untitled|new workflow)\b", re.I)

SYSTEM_RULES = [
    ("Lifecycle & Stage Management", r"lifecycle|mql|sql|stage|sqo|funnel|handoff|hand-off"),
    ("Lead Routing & Assignment", r"rout|assign|owner|territor|rotat|round.?robin|distribut"),
    ("Lead Scoring & Qualification", r"scor|grade|fit|qualif|icp|tier|rating"),
    ("Deliverability & Suppression", r"bounce|unsub|suppress|opt.?out|deliverab|spam|gdpr|ccpa|consent"),
    ("Nurture & Marketing Campaigns", r"nurture|drip|campaign|newsletter|webinar|promo|re.?engag|welcome|onboard.*email"),
    ("Data Hygiene & Automation", r"clean|hygien|normal|standard|dedup|format|enrich|backfill|fix|correct"),
    ("Internal Notifications & Tasks", r"notif|alert|slack|email.*team|internal|escalat"),
    ("Sales & Deal Automation", r"deal|pipeline|quote|contract|renewal|churn|upsell|opportunit"),
    ("Customer Onboarding & Success", r"onboard|activation|adoption|csm|success|nps|survey"),
    ("Integrations & App Actions", r"sync|salesforce|sfdc|integrat|zapier|api|webhook|import"),
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

        # key -> the label HubSpot shows in its own UI. Where two objects use the
        # same label, the object is appended so the two stay tellable apart.
        raw_labels: dict[str, str] = {}
        label_counts: Counter[str] = Counter()
        for obj, props in self.properties.items():
            for prop in props:
                label = (prop.get("label") or prop["name"]).strip()
                raw_labels[f"{obj}.{prop['name']}"] = label
                label_counts[label] += 1
        self.prop_labels = {
            key: (label if label_counts[label] == 1 else f"{label} ({key.split('.')[0]})")
            for key, label in raw_labels.items()
        }

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

    def qualify(self, name: str, object_type: str | None) -> str:
        """Resolve a bare property name to `object.name`.

        Prefers the object the referencing asset operates on; falls back to the
        only object that defines the name, and finally to the first match.
        """
        if object_type and name in self.known_props.get(object_type, set()):
            return f"{object_type}.{name}"
        owners = [obj for obj, names in self.known_props.items() if name in names]
        if len(owners) == 1:
            return f"{owners[0]}.{name}"
        for obj in ("contacts", "companies", "deals"):
            if obj in owners:
                return f"{obj}.{name}"
        return f"{owners[0]}.{name}" if owners else f"?.{name}"

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
            # The team's own words, written in HubSpot. Authoritative where present:
            # a generated summary says what a workflow does, never why it exists.
            "hubspot_description": (flow.get("description") or "").strip(),
            "enrolled_total": flow.get("_enrolled_total"),
            "enrolled_active": flow.get("_enrolled_active"),
            # Operational history, only present when a workflow listing export was merged.
            "last_action_at": flow.get("_export_last_action_at"),
            "enrolled_7d": flow.get("_export_enrolled_7d"),
            "enrolled_runs": flow.get("_export_enrolled_runs"),
            "open_issues": flow.get("_export_open_issues"),
            "last_issue_at": flow.get("_export_last_issue_at"),
            "trigger_summary": flow.get("_export_trigger_type"),
            "built_in": flow.get("_export_built_in"),
            "created_by": flow.get("_export_created_by"),
            "updated_by": flow.get("_export_updated_by"),
            "brand": flow.get("_export_brand"),
            "used_elsewhere": flow.get("_export_used_elsewhere"),
            "export_action_types": flow.get("_export_action_types") or [],
            "in_export": flow.get("_export_present"),
            "export_only": bool(flow.get("_export_only")),
            "time_windows": _time_windows(flow.get("timeWindows") or []),
            "blocked_dates": len(flow.get("blockedDates") or []),
            "associations_used": len([d for d in (flow.get("dataSources") or [])
                                      if d.get("type", "").startswith("ASSOCIATION")]),
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
            "properties_read_labels": [],
            "properties_written_labels": [],
            "properties_read_q": sorted(
                {self.qualify(n, OBJECT_BY_TYPE_ID.get(str(flow.get("objectTypeId")))) for n in read}
            ),
            "properties_written_q": sorted(
                {self.qualify(n, OBJECT_BY_TYPE_ID.get(str(flow.get("objectTypeId")))) for n in written}
            ),
            "lists_referenced": sorted(refs["lists"]),
            "emails_referenced": sorted(refs["emails"]),
            "workflows_triggered": sorted(refs["flows"]),
            "forms_referenced": sorted(refs["forms"]),
            "suppression_lists": [str(x) for x in (flow.get("suppressionListIds") or [])],
        }
        record["properties_written_labels"] = self._labels(record["properties_written_q"])
        record["properties_read_labels"] = self._labels(record["properties_read_q"])
        record["steps_text"] = self._describe_steps(record)
        record["description"] = " ".join(record["steps_text"])

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
            elif a_type.upper() == "CUSTOM_CODE":
                label = "Custom code"
            else:
                label = self._infer_action(action, a_type, type_id)
            summary.append({"id": action.get("actionId"), "label": label, "type_id": type_id})
        return summary, branches

    def _infer_action(self, action: dict[str, Any], a_type: str, type_id: str) -> str:
        """Name an unrecognised action from its payload rather than guessing.

        A `1-` type ID prefix marks a third-party app extension action; the field
        keys then say which app. Anything still unidentified is reported by raw ID
        and collected for the report's caveats.
        """
        fields = set(action.get("fields") or {})
        if type_id.startswith("1-"):
            self.unknown_action_types[type_id] += 1
            return f"App action ({_app_hint(fields)})" if fields else "App action"
        for keys, label in ACTION_FIELD_HINTS:
            if fields & keys:
                return label
        if type_id:
            self.unknown_action_types[type_id] += 1
            return f"{a_type or 'Action'} ({type_id})"
        return a_type or "Action"

    def label(self, key: str) -> str:
        """The name a person recognises, falling back to the internal one."""
        return self.prop_labels.get(key, key)

    def _labels(self, keys: list[str]) -> list[str]:
        return [self.label(k) for k in keys]

    def _describe_steps(self, r: dict[str, Any]) -> list[str]:
        """What this workflow does, as short numbered points rather than a paragraph."""
        if not r["definition_available"]:
            return self._describe_from_export(r)

        obj = _object_label(r["object_type"])
        state = "Active" if r["enabled"] else "Turned off"
        out = [f"{state} {obj} workflow."]
        if r.get("hubspot_description"):
            out.append(f"Your own note in HubSpot: “{r['hubspot_description']}”")

        reads = self._labels(r["properties_read_q"])
        if reads:
            shown = ", ".join(reads[:6])
            more = f" (+{len(reads) - 6} more)" if len(reads) > 6 else ""
            out.append(f"Enrols and branches on: {shown}{more}.")
        elif r["enrollment_type"]:
            out.append(f"Enrolment type: {r['enrollment_type']}.")

        writes = self._labels(r["properties_written_q"])
        if writes:
            shown = ", ".join(writes[:6])
            more = f" (+{len(writes) - 6} more)" if len(writes) > 6 else ""
            out.append(f"Writes: {shown}{more}.")

        counts = Counter(a["label"] for a in r["actions"])
        if counts:
            steps = ", ".join(f"{n}x {label}" for label, n in counts.most_common(8))
            out.append(f"{r['action_count']} steps: {steps}.")

        out.extend(_activity_lines(r))

        if r.get("time_windows"):
            out.append(f"Only runs {r['time_windows']}."
                       + (f" {r['blocked_dates']} blocked dates." if r.get("blocked_dates") else ""))

        tail = []
        if r["workflows_triggered"]:
            tail.append(f"hands off to {len(r['workflows_triggered'])} other workflow(s)")
        if r["suppression_lists"]:
            tail.append(f"{len(r['suppression_lists'])} suppression list(s) applied")
        if r["re_enrollment"]:
            tail.append("re-enrolment is on")
        if tail:
            out.append(_sentence(tail) + ".")
        return out

    def _describe_from_export(self, r: dict[str, Any]) -> list[str]:
        """All we can honestly say about a workflow whose definition we could not read.

        For one created after the snapshot that is still a lot: HubSpot's own export
        carries the name, the team's description, the action types and the activity.
        """
        obj = _object_label(r["object_type"])
        state = "Active" if r["enabled"] else "Turned off"
        if r.get("export_only"):
            out = [f"{state} {obj} workflow, created after this audit's snapshot was taken, "
                   "so the step-by-step below comes from HubSpot's workflow export rather "
                   "than a full read of the definition."]
        else:
            out = [f"{state} {obj} workflow. The full definition could not be read from "
                   "HubSpot, so only what follows is known."]
        if r.get("hubspot_description"):
            out.append(f"Your own note in HubSpot: “{r['hubspot_description']}”")
        if r.get("trigger_summary"):
            out.append(f"Starts: {r['trigger_summary'].lower()}.")
        types = r.get("export_action_types") or []
        if types:
            shown = ", ".join(types[:8])
            more = f" (+{len(types) - 8} more kinds)" if len(types) > 8 else ""
            out.append(f"Uses these kinds of step: {shown}{more}.")
        out.extend(_activity_lines(r))
        return out

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
                "fields_q": sorted({self.qualify(n, "contacts") for n in fields}),
                "fields_labels": self._labels(sorted({self.qualify(n, "contacts") for n in fields})),
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
                "properties_q": sorted(
                    {self.qualify(n, OBJECT_BY_TYPE_ID.get(str(lst.get("objectTypeId")))) for n in props}
                ),
                "properties_labels": self._labels(sorted(
                    {self.qualify(n, OBJECT_BY_TYPE_ID.get(str(lst.get("objectTypeId")))) for n in props}
                )),
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
                    "key": f"{obj_type}.{name}",
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
                    "display": self.label(f"{obj_type}.{name}"),
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
            systems[classify_workflow(wf)].append(wf)
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


APP_HINTS = [
    ({"slackActions", "slackUserIds", "messageMentions"}, "Slack"),
    ({"project", "issueType"}, "Jira"),
    ({"Workspace", "Space", "Folder"}, "ClickUp"),
    ({"spreadsheet", "sheet"}, "Google Sheets"),
    ({"Phone_Number"}, "phone lookup"),
    ({"templateName"}, "template"),
]


def _app_hint(fields: set[str]) -> str:
    for keys, name in APP_HINTS:
        if fields & keys:
            return name
    return "third-party"


# Property names that identify what a workflow is for, checked against the bare
# name so an object prefix does not matter.
BEHAVIOUR_RULES = [
    ("Lifecycle & Stage Management", {"lifecyclestage", "hs_lead_status"}, set()),
    ("Lead Routing & Assignment", {"hubspot_owner_id"}, {"0-11"}),
    ("Lead Scoring & Qualification", set(), set()),   # handled by pattern below
    ("Sales & Deal Automation", {"dealstage", "pipeline", "amount", "closedate"}, set()),
    ("Nurture & Marketing Campaigns", set(), {"0-4", "0-46510720"}),
    ("Record Creation & Association", set(), {"0-14", "0-63189541"}),
    ("Internal Notifications & Tasks", set(), {"0-3", "0-8"}),
]

SCORE_PATTERN = re.compile(r"score|grade|tier|icp|rating|qualif", re.I)


def _classify(name: str) -> str:
    """Name-based classification, used only when the name carries meaning."""
    lowered = (name or "").lower()
    for label, pattern in SYSTEM_RULES:
        if re.search(pattern, lowered):
            return label
    return ""


def classify_workflow(record: dict[str, Any]) -> str:
    """Decide which system a workflow belongs to.

    A meaningful name wins, because the admin's own label is the best evidence of
    intent. Portals routinely carry dozens of auto-named workflows, though, so
    behaviour — the properties written, the object enrolled, the actions taken —
    is the fallback rather than a shrug.
    """
    name = record.get("name") or ""
    if not AUTO_NAME.match(name):
        by_name = _classify(name)
        if by_name:
            return by_name

    # A workflow with no steps and no property references is an empty shell, not an
    # unclassifiable one. Naming it as such makes it show up as the finding it is.
    if not record.get("action_count") and not record.get("properties_written") \
            and not record.get("properties_read"):
        return "Empty — no steps configured"

    written = {p.split(".")[-1] for p in record.get("properties_written", [])}
    read = {p.split(".")[-1] for p in record.get("properties_read", [])}
    type_ids = {a.get("type_id") for a in record.get("actions", [])}
    object_type = str(record.get("object_type") or "")

    if SCORE_PATTERN.search(" ".join(written)):
        return "Lead Scoring & Qualification"
    for label, props, actions in BEHAVIOUR_RULES:
        if props and written & props:
            return label
        if actions and type_ids & actions:
            return label
    if object_type == "0-5":
        return "Support & Ticketing"
    if any(str(t).startswith("1-") for t in type_ids if t):
        return "Integrations & App Actions"
    if object_type == "0-3":
        return "Sales & Deal Automation"
    if written:
        return "Data Hygiene & Automation"
    if read or record.get("action_count"):
        return "Other Automation"
    return "Unclassified"


DAY_SHORT = {"MONDAY": "Mon", "TUESDAY": "Tue", "WEDNESDAY": "Wed", "THURSDAY": "Thu",
             "FRIDAY": "Fri", "SATURDAY": "Sat", "SUNDAY": "Sun"}


def _time_windows(windows: list[dict[str, Any]]) -> str:
    """Execution windows, as a person would say them.

    A workflow restricted to weekday mornings behaves very differently from one
    that runs continuously, and nothing else in the definition reveals it.
    """
    if not windows:
        return ""
    spans: dict[tuple[str, str], list[str]] = {}
    for window in windows:
        start = window.get("startTime") or {}
        end = window.get("endTime") or {}
        span = (f"{start.get('hour', 0):02d}:{start.get('minute', 0):02d}",
                f"{end.get('hour', 0):02d}:{end.get('minute', 0):02d}")
        spans.setdefault(span, []).append(DAY_SHORT.get(window.get("day", ""), window.get("day", "")))
    return "; ".join(f"{', '.join(days)} {a}–{b}" for (a, b), days in spans.items())


def _sentence(parts: list[str]) -> str:
    """Join clauses into one readable sentence, capitalised."""
    if len(parts) == 1:
        joined = parts[0]
    else:
        joined = ", ".join(parts[:-1]) + " and " + parts[-1]
    return joined[0].upper() + joined[1:]


def _activity_lines(r: dict[str, Any]) -> list[str]:
    """What this workflow has actually been doing, in plain sentences.

    Enrolment counts come from the Automation API; the dates and the seven-day figure
    come from a merged workflow export. Either can be absent, and an absent number is
    never written as a zero — "we did not measure it" and "it never happened" are
    different answers and a reader will act on them differently.
    """
    out: list[str] = []
    total, active = r.get("enrolled_total"), r.get("enrolled_active")
    last = str(r.get("last_action_at") or "")[:10]

    if total == 0:
        out.append("Has never enrolled a single record since it was created.")
    elif total:
        line = f"Has enrolled {total:,} records in its lifetime"
        line += f", {active:,} currently in it" if active else ", none in it now"
        out.append(line + ".")

    if last:
        recent = r.get("enrolled_7d")
        line = f"Last did something on {last}"
        if recent:
            line += f", and {recent:,} records went through it in the last seven days"
        elif recent == 0:
            line += ", and nothing has gone through it in the last seven days"
        out.append(line + ".")
    elif total:
        out.append("No record of when it last ran.")

    if r.get("in_export") is False:
        out.append("Not present in the workflow export taken after this snapshot, so it may "
                   "have been deleted from HubSpot since.")

    issues = r.get("open_issues")
    if issues:
        when = str(r.get("last_issue_at") or "")[:10]
        out.append(f"HubSpot is currently reporting {issues} problem(s) with it"
                   + (f", the most recent on {when}." if when else "."))
    return out


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
        "workflow_export": snapshot.get("workflow_export"),
        "workflows": workflows,
        "properties": properties,
        "forms": forms,
        "lists": lists_,
        "marketing_emails": _describe_assets(
            _simple_assets(snapshot.get("marketing_emails", []), a.portal_id,
                           links.marketing_email, "email"),
            workflows, "email",
        ),
        "landing_pages": _describe_assets(
            _simple_assets(snapshot.get("landing_pages", []), a.portal_id, links.page,
                           "landing page"), workflows, "page",
        ),
        "site_pages": _describe_assets(
            _simple_assets(snapshot.get("site_pages", []), a.portal_id, links.page, "site page"),
            workflows, "page",
        ),
        "blog_posts": _simple_assets(
            snapshot.get("blog_posts", []), a.portal_id, links.blog_post, "blog post"
        ),
        "owners": snapshot.get("owners", []),
        "pipelines": snapshot.get("pipelines", {}),
        "systems": {k: [w["id"] for w in v] for k, v in systems.items()},
        "clusters": clusters,
        "skipped": snapshot.get("skipped", []),
        "property_labels": a.prop_labels,
        "coverage": a.coverage,
        "usage_complete": a.usage_complete,
        "unknown_action_types": dict(a.unknown_action_types),
    }


# Words that appear in campaign names and reliably say what an email is for. Order
# matters: the first match wins, so the more specific patterns come first.
PURPOSE_HINTS = [
    (r"\bwelcome|onboard|getting started|day\s*[01]\b", "Welcome / onboarding"),
    (r"\babandon|cart|incomplete|unfinished", "Abandoned-action recovery"),
    (r"\bre.?engage|win.?back|churn|dormant|inactive|we miss", "Re-engagement"),
    (r"\bnewsletter|digest|round.?up|monthly|weekly|bulletin", "Newsletter / digest"),
    (r"\bwebinar|event|invite|invitation|rsvp|register", "Event or webinar"),
    (r"\bpromo|offer|discount|sale|deal of|black friday|cyber", "Promotion / offer"),
    (r"\breminder|follow.?up|nudge|expiring|expires|renewal", "Reminder / follow-up"),
    (r"\breceipt|invoice|order|shipping|confirmation|confirmed", "Transactional confirmation"),
    (r"\bsurvey|feedback|nps|review|rate us", "Survey / feedback"),
    (r"\bannounce|launch|introducing|new feature|release|update", "Announcement"),
    (r"\bnurture|drip|sequence|series|part\s*\d", "Nurture sequence"),
    (r"\bdemo|trial|pricing|quote|proposal|sales", "Sales outreach"),
    (r"\bthank|thanks", "Thank-you"),
    (r"\bdemo request|contact us|enquiry|inquiry|lead", "Lead capture"),
]


def _purpose(name: str, subject: str, kind: str) -> str:
    """A short, honest read of what a marketing asset is for.

    Inferred from the words the team themselves put in the name and subject, so it
    reflects their own vocabulary rather than an outside guess.
    """
    haystack = f"{name} {subject}".lower()
    for pattern, label in PURPOSE_HINTS:
        if re.search(pattern, haystack):
            return label
    return "Uncategorised " + ("email" if kind == "email" else "page")


def _describe_assets(assets: list[dict[str, Any]], workflows: list[dict[str, Any]],
                     kind: str) -> list[dict[str, Any]]:
    """Add a purpose line, and name the workflows that actually send each email.

    The sending workflow is a fact read from the account; the category is an
    inference from wording. The two are kept in separate fields so a reader can see
    which is which.
    """
    senders: dict[str, list[str]] = {}
    for w in workflows:
        for email_id in w.get("emails_referenced") or []:
            senders.setdefault(str(email_id), []).append(w["name"])

    for asset in assets:
        sent_by = senders.get(asset["id"], [])
        asset["purpose"] = _purpose(asset.get("name") or "", asset.get("subject") or "", kind)
        asset["sent_by"] = sent_by
        state = (asset.get("state") or "").upper()
        if sent_by:
            asset["about"] = (
                f"{asset['purpose']}. Sent automatically by "
                + ", ".join(f"“{n}”" for n in sent_by[:3])
                + (f" and {len(sent_by) - 3} more workflow(s)." if len(sent_by) > 3 else ".")
            )
        elif kind == "email":
            asset["about"] = (
                f"{asset['purpose']}. No workflow sends this — it was a one-off send"
                + (" and is still a draft." if "DRAFT" in state else " or is sent by hand.")
            )
        else:
            asset["about"] = (
                f"{asset['purpose']}."
                + (" Published and live." if "PUBLISH" in state else " Not currently published.")
            )
    return assets


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
