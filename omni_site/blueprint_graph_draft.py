"""Deterministic, non-executable Graph Studio draft from a validated Blueprint."""
from __future__ import annotations

from typing import Any

from omni_site.blueprint_plan_import import validate_plan


def graph_draft(content: bytes) -> dict[str, Any]:
    """Convert planning components to layout nodes, never runnable actions."""
    import json

    preview = validate_plan(content)
    plan = json.loads(content)
    architecture = plan["architecture"]
    nodes = [
        {
            "id": item["id"],
            "type": "note",
            "label": item["label"],
            "position": {"x": 80 + (index % 3) * 320, "y": 100 + (index // 3) * 190},
            "config": {"description": item["label"], "executable": False},
        }
        for index, item in enumerate(architecture["nodes"])
    ]
    edges = [
        {
            "id": f"edge-{index:03d}",
            "source": item["source"],
            "target": item["target"],
            "type": "reference",
            "executable": False,
        }
        for index, item in enumerate(architecture["links"], 1)
    ]
    return {
        "schema": "omnifactory.graph.draft.v1",
        "source_schema": "omnifactory.blueprint.plan.v1",
        "source_revision": preview.revision,
        "status": "design_only",
        "executable": False,
        "requires_review": True,
        "nodes": nodes,
        "edges": edges,
        "integrations": [
            {"id": item["id"], "name": item["name"], "connected": False}
            for item in architecture["integrations"]
        ],
        "summary": {
            "milestones": preview.milestones,
            "checks": preview.checks,
            "risks": preview.risks,
        },
    }
