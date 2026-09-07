"""A directed influence graph over every asset in the portal.

One edge direction throughout: A → B means "a change to A can change B".
That single convention makes both questions the audit exists to answer fall out
of the same traversal:

    downstream(X)  what could break if I edit X
    upstream(X)    what X depends on, and who else writes to it

A workflow influences the properties it writes; a property influences the
workflows that read it and the lists that segment on it; a list influences the
workflows that enrol from it. Following those edges transitively is the blast
radius.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable

from . import links

# Edge label -> (verb shown downstream, verb shown upstream)
RELATIONS = {
    "writes": ("writes", "written by"),
    "reads": ("read by", "reads"),
    "segments": ("segments", "segmented on by"),
    "enrolls": ("enrols", "enrols from"),
    "suppresses": ("suppresses", "suppressed by"),
    "sends": ("sends", "sent by"),
    "triggers": ("triggers", "triggered by"),
    "collects": ("collects into", "collected by"),
    "hosts": ("hosts", "hosted on"),
    "stages": ("provides stage", "stage of"),
}

TYPE_PLURALS = {
    "workflow": "Workflows",
    "property": "Properties",
    "list": "Lists",
    "form": "Forms",
    "email": "Marketing emails",
    "page": "Pages",
    "pipeline": "Pipelines",
    "stage": "Pipeline stages",
}

TYPE_LABELS = {
    "workflow": "Workflow",
    "property": "Property",
    "list": "List",
    "form": "Form",
    "email": "Marketing email",
    "page": "Page",
    "pipeline": "Pipeline",
    "stage": "Pipeline stage",
}


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.out: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.inc: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_node(self, node_id: str, **attrs: Any) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].update({k: v for k, v in attrs.items() if v is not None})
        else:
            self.nodes[node_id] = dict(attrs)

    def add_edge(self, src: str, dst: str, relation: str) -> None:
        if src == dst or src not in self.nodes or dst not in self.nodes:
            return
        if (dst, relation) not in self.out[src]:
            self.out[src].append((dst, relation))
            self.inc[dst].append((src, relation))

    # ------------------------------------------------------------- traversal

    def _walk(self, start: str, adjacency, max_depth: int) -> dict[str, int]:
        """Breadth-first reachability with the depth each node was first found at."""
        seen: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbour, _ in adjacency.get(node, []):
                if neighbour == start or neighbour in seen:
                    continue
                seen[neighbour] = depth + 1
                queue.append((neighbour, depth + 1))
        return seen

    def downstream(self, node_id: str, max_depth: int = 4) -> dict[str, int]:
        return self._walk(node_id, self.out, max_depth)

    def upstream(self, node_id: str, max_depth: int = 4) -> dict[str, int]:
        return self._walk(node_id, self.inc, max_depth)

    def impact(self, node_id: str, max_depth: int = 4) -> dict[str, Any]:
        """Everything a change to this node could reach, grouped by asset type."""
        reach = self.downstream(node_id, max_depth)
        by_type: dict[str, list[str]] = defaultdict(list)
        for target, _ in reach.items():
            by_type[self.nodes[target]["type"]].append(target)
        return {
            "total": len(reach),
            "direct": len(self.out.get(node_id, [])),
            "by_type": {k: sorted(v) for k, v in by_type.items()},
            "depths": reach,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [
                {"from": src, "to": dst, "rel": rel}
                for src, targets in self.out.items()
                for dst, rel in targets
            ],
        }


# ------------------------------------------------------------------- building


def _pid(analysis: dict[str, Any]) -> str:
    return str(analysis.get("portal_id", ""))


def build(analysis: dict[str, Any]) -> Graph:
    g = Graph()
    portal = _pid(analysis)

    # -- nodes -------------------------------------------------------------
    for p in analysis["properties"]:
        g.add_node(
            f"prop:{p['key']}",
            type="property",
            label=p["key"],
            name=p["name"],
            display=p.get("label") or p["name"],
            object_type=p["object_type"],
            link=p["link"],
            custom=not p["hubspot_defined"],
            field_type=p.get("field_type") or p.get("type"),
            group=p.get("group"),
            note=p.get("description") or "",
        )

    for w in analysis["workflows"]:
        g.add_node(
            f"wf:{w['id']}",
            type="workflow",
            label=w["name"],
            link=w["link"],
            enabled=w["enabled"],
            note=w["description"],
            updated=w.get("updated_at"),
            steps=w.get("action_count", 0),
        )

    for l in analysis["lists"]:
        g.add_node(
            f"list:{l['id']}",
            type="list",
            label=l["name"],
            link=l["link"],
            note=l["description"],
            processing=l.get("processing_type"),
            size=l.get("size"),
        )

    for f in analysis["forms"]:
        g.add_node(
            f"form:{f['id']}",
            type="form",
            label=f["name"],
            link=f["link"],
            note=f["description"],
            archived=f.get("archived", False),
        )

    for e in analysis["marketing_emails"]:
        g.add_node(
            f"email:{e['id']}",
            type="email",
            label=e["name"],
            link=e["link"],
            note=e.get("subject") or "",
            state=e.get("state"),
        )

    for page in analysis["landing_pages"] + analysis["site_pages"]:
        g.add_node(
            f"page:{page['id']}",
            type="page",
            label=page["name"],
            link=page["link"],
            note=page.get("url") or "",
            state=page.get("state"),
            kind=page.get("kind"),
        )

    for obj, pipelines in (analysis.get("pipelines") or {}).items():
        for pl in pipelines:
            pl_id = f"pipeline:{obj}:{pl.get('id')}"
            g.add_node(
                pl_id,
                type="pipeline",
                label=pl.get("label") or pl.get("id"),
                link=links.pipeline(portal, obj),
                note=f"{obj} pipeline",
                object_type=obj,
            )
            for stage in pl.get("stages", []) or []:
                st_id = f"stage:{pl.get('id')}:{stage.get('id')}"
                g.add_node(
                    st_id,
                    type="stage",
                    label=stage.get("label") or stage.get("id"),
                    link=links.pipeline(portal, obj),
                    note=f"stage of {pl.get('label')}",
                )
                g.add_edge(pl_id, st_id, "stages")

    # -- edges -------------------------------------------------------------
    for w in analysis["workflows"]:
        wid = f"wf:{w['id']}"
        for key in w.get("properties_written_q") or []:
            g.add_edge(wid, f"prop:{key}", "writes")
        for key in w.get("properties_read_q") or []:
            g.add_edge(f"prop:{key}", wid, "reads")
        for list_id in w.get("lists_referenced") or []:
            g.add_edge(f"list:{list_id}", wid, "enrolls")
        for list_id in w.get("suppression_lists") or []:
            g.add_edge(f"list:{list_id}", wid, "suppresses")
        for email_id in w.get("emails_referenced") or []:
            g.add_edge(wid, f"email:{email_id}", "sends")
        for target in w.get("workflows_triggered") or []:
            g.add_edge(wid, f"wf:{target}", "triggers")

    for f in analysis["forms"]:
        for key in f.get("fields_q") or []:
            g.add_edge(f"form:{f['id']}", f"prop:{key}", "collects")

    for l in analysis["lists"]:
        for key in l.get("properties_q") or []:
            g.add_edge(f"prop:{key}", f"list:{l['id']}", "segments")

    # A deal-stage property's values are the pipeline stages it can hold.
    for obj, pipelines in (analysis.get("pipelines") or {}).items():
        prop_key = "deals.dealstage" if obj == "deals" else f"{obj}.hs_pipeline_stage"
        for pl in pipelines:
            for stage in pl.get("stages", []) or []:
                g.add_edge(f"prop:{prop_key}", f"stage:{pl.get('id')}:{stage.get('id')}", "stages")

    return g


def summarize(g: Graph) -> dict[str, Any]:
    """Portal-level graph statistics, and the assets with the widest blast radius."""
    counts: dict[str, int] = defaultdict(int)
    for node in g.nodes.values():
        counts[node["type"]] += 1

    riskiest = []
    for node_id, node in g.nodes.items():
        if node["type"] != "workflow":
            continue
        impact = g.impact(node_id)
        if impact["total"]:
            riskiest.append((node_id, node["label"], impact["total"], impact["direct"]))
    riskiest.sort(key=lambda r: -r[2])

    orphans = [
        node_id for node_id, node in g.nodes.items()
        if node["type"] in ("property", "list", "form", "email")
        and not g.out.get(node_id) and not g.inc.get(node_id)
    ]

    return {
        "node_counts": dict(counts),
        "edge_count": sum(len(v) for v in g.out.values()),
        "riskiest_workflows": riskiest[:15],
        "orphan_count": len(orphans),
    }
