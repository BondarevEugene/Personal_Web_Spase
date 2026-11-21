"""Deterministic, read-only evidence for a saved Graph Studio release.

No cloud side effects, bot tokens or unverifiable online status.
"""
from __future__ import annotations

from collections import deque

from api.simple_builder import Scenario, release_preflight


def graph_inventory(scenario: Scenario) -> dict:
    by_id = {node.id: node for node in scenario.nodes}
    queue = deque([scenario.start])
    reachable = set()
    edges = []
    while queue:
        node_id = queue.popleft()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        node = by_id[node_id]
        outgoing = []
        if node.kind == "choice":
            outgoing = [(option.target, "button") for option in node.options]
        elif node.kind == "condition":
            outgoing = [(node.true_target, "true"), (node.false_target, "false")]
        elif node.next:
            outgoing = [(node.next, "next")]
        for target, label in outgoing:
            edges.append({"source": node_id, "target": target, "kind": label})
            if target not in reachable:
                queue.append(target)
    counts = {}
    for node in scenario.nodes:
        counts[node.kind] = counts.get(node.kind, 0) + 1
    return {
        "node_count": len(scenario.nodes),
        "reachable_count": len(reachable),
        "unreachable_nodes": sorted(set(by_id) - reachable),
        "node_types": dict(sorted(counts.items())),
        "edges": sorted(edges, key=lambda e: (e["source"], e["target"], e["kind"])),
        "terminal_nodes": sorted(n.id for n in scenario.nodes if n.kind == "end" and n.id in reachable),
    }


def release_evidence(scenario: Scenario, project_id: str, revision: str) -> dict:
    inventory = graph_inventory(scenario)
    preflight = release_preflight(scenario)
    blockers = [issue for issue in preflight["issues"] if issue["severity"] == "error"]
    warnings = [issue for issue in preflight["issues"] if issue["severity"] != "error"]
    return {
        "project_id": project_id,
        "revision": revision,
        "scenario_name": scenario.name,
        "inventory": inventory,
        "preflight": preflight,
        "blockers": blockers,
        "warnings": warnings,
        "export_ready": preflight["ready"],
        "manual_launch_required": True,
        "live_deployment_verified": False,
        "evidence_scope": "saved_graph_static_analysis",
        "next_action": (
            "export_and_configure_hosting" if preflight["ready"]
            else "fix_graph_and_save_revision"
        ),
    }
