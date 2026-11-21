"""Explicit, authenticated Blueprint -> editable Telegram Graph Studio project.

Planning components are mapped to message placeholders, never API actions.
"""
from __future__ import annotations

import json
from collections import deque

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.builder_projects import ProjectData, create_project
from api.simple_builder import Scenario
from omni_site.blueprint_plan_import import MAX_BYTES, PlanValidationError, validate_plan

router = APIRouter(tags=["Blueprint Graph Studio import"])


def build_editable_graph(content: bytes, name: str) -> ProjectData:
    """Convert an acyclic, connected planning graph to a valid aiogram draft."""
    validate_plan(content)
    if not 2 <= len(name.strip()) <= 100:
        raise PlanValidationError("Project name must contain 2–100 characters")
    architecture = json.loads(content)["architecture"]
    components = architecture["nodes"]
    if not components or len(components) > 79:
        raise PlanValidationError("Graph needs 1–79 planning components")
    by_id = {node["id"]: node for node in components}
    successors: dict[str, list[str]] = {key: [] for key in by_id}
    incoming: dict[str, int] = dict.fromkeys(by_id, 0)
    for edge in architecture["links"]:
        source, target = edge["source"], edge["target"]
        if target in successors[source]:
            raise PlanValidationError("Duplicate architecture link")
        successors[source].append(target)
        incoming[target] += 1
    roots = [key for key, degree in incoming.items() if degree == 0]
    if len(roots) != 1:
        raise PlanValidationError("Expected one starting component")
    queue = deque(roots)
    ordered: list[str] = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for target in successors[current]:
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    if len(ordered) != len(components):
        raise PlanValidationError("Disconnected or cyclic architecture")
    # A choice is a real, editable Telegram button block. Reject graphs
    # exceeding the builder's supported eight choices per decision.
    if any(len(targets) > 8 for targets in successors.values()):
        raise PlanValidationError("Maximum eight branches per component")
    node_ids = {key: f"step{index + 1:03d}" for index, key in enumerate(ordered)}
    nodes = []
    positions = {}
    for index, key in enumerate(ordered):
        label = by_id[key]["label"]
        if not isinstance(label, str) or not label.strip():
            raise PlanValidationError("Empty architecture component")
        node_id = node_ids[key]
        targets = successors[key]
        if len(targets) > 1:
            # Button labels are explicit placeholders, not inferred business rules.
            node = {
                "id": node_id,
                "kind": "choice",
                "text": f"Выберите маршрут: {label}"[:1500],
                "options": [
                    {
                        "label": f"Вариант {number}: {by_id[target]['label']}"[:64],
                        "target": node_ids[target],
                    }
                    for number, target in enumerate(targets, 1)
                ],
            }
        else:
            node = {
                "id": node_id,
                "kind": "message",
                "text": f"Этап проекта: {label}"[:1500],
                "next": node_ids[targets[0]] if targets else "finish",
            }
        nodes.append(node)
        positions[node_id] = {
            "x": 80 + (index % 3) * 300,
            "y": 100 + (index // 3) * 170,
        }
    nodes.append({"id": "finish", "kind": "end"})
    positions["finish"] = {
        "x": 80 + (len(ordered) % 3) * 300,
        "y": 100 + (len(ordered) // 3) * 170,
    }
    return ProjectData(
        scenario=Scenario.model_validate({
            "name": name.strip(), "start": "step001", "nodes": nodes,
        }),
        positions=positions,
    )


@router.post("/api/v1/blueprint/import-graph", status_code=201)
async def import_blueprint_graph(
    request: Request,
    plan_file: UploadFile = File(...),
    name: str = Form(..., min_length=2, max_length=100),
    confirm_placeholders: bool = Form(False),
):
    """Persist a user-confirmed editable graph through existing auth/CSRF path."""
    if not confirm_placeholders:
        raise HTTPException(422, "Confirm that planning nodes become editable messages")
    if plan_file.content_type not in (
        "application/json", "text/plain", "application/octet-stream",
    ):
        raise HTTPException(415, "JSON file required")
    try:
        content = await plan_file.read(MAX_BYTES + 1)
        project = build_editable_graph(content, name)
    except PlanValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await plan_file.close()
    result = create_project(request, project)
    return {
        **result,
        "url": f"/account/graph-project/{result['id']}",
        "status": "saved_editable_draft",
        "deployable": False,
        "review_required": True,
        "notice": "Planning components are message placeholders, not integrations.",
    }
