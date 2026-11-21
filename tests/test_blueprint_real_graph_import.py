"""Real Blueprint -> saved Graph Studio import contract."""
import json

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_graph_import import build_editable_graph
from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from server import app

CLIENT = TestClient(app)
URL = "/api/v1/blueprint/import-graph"


def plan(sector="telegram"):
    spec = compile_specification(
        sector=sector, team="growth", process="manual", priority="control",
    )
    sections = build_project_plan(spec)
    return {
        "schema": "omnifactory.blueprint.plan.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "architecture": sections.architecture,
        "milestones": sections.milestones,
        "verification": sections.verification,
        "risks": sections.risks,
    }


def upload(data, confirmed=True):
    return CLIENT.post(
        URL,
        data={"name": "Мой проект", "confirm_placeholders": str(confirmed).lower()},
        files={"plan_file": ("blueprint.json", json.dumps(data), "application/json")},
    )


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_conversion_is_editable_valid_and_preserves_component_labels(sector):
    source = plan(sector)
    result = build_editable_graph(
        json.dumps(source, ensure_ascii=False).encode(), "Мой проект",
    )
    scenario = result.scenario
    assert scenario.start == "step001"
    assert len(scenario.nodes) == len(source["architecture"]["nodes"]) + 1
    assert scenario.nodes[-1].kind == "end"
    assert all(node.kind == "message" for node in scenario.nodes[:-1])
    assert all(
        node.text.endswith(component["label"])
        for node, component in zip(
            scenario.nodes[:-1], source["architecture"]["nodes"], strict=True,
        )
    )
    assert set(result.positions) == {node.id for node in scenario.nodes}
    assert result.checked_positions()
    assert scenario.model_validate(scenario.model_dump())


def test_anonymous_cannot_save_graph():
    assert upload(plan()).status_code == 401


def test_explicit_confirmation_is_required():
    assert upload(plan(), confirmed=False).status_code == 422


def test_import_rejects_cyclic_or_branched_architecture():
    source = plan()
    source["architecture"]["links"].append({
        "source": source["architecture"]["nodes"][-1]["id"],
        "target": source["architecture"]["nodes"][0]["id"],
    })
    with pytest.raises(ValueError):
        build_editable_graph(json.dumps(source).encode(), "Мой проект")


def test_import_form_and_script_are_present():
    response = CLIENT.get("/demo/blueprint")
    assert response.status_code == 200
    assert 'id="blueprint-graph-import-form"' in response.text
    assert "blueprint_graph_import.js" in response.text
