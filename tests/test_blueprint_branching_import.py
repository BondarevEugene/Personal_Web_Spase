"""Branching Blueprint DAGs become real Graph Studio choice nodes."""
import json

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_graph_import import build_editable_graph
from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from server import app

client = TestClient(app)


def plan():
    spec = compile_specification(
        sector="telegram", team="growth", process="manual", priority="control",
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


def branched():
    data = plan()
    nodes = data["architecture"]["nodes"]
    assert len(nodes) >= 4
    data["architecture"]["links"] = [
        {"source": nodes[0]["id"], "target": nodes[1]["id"]},
        {"source": nodes[0]["id"], "target": nodes[2]["id"]},
        {"source": nodes[1]["id"], "target": nodes[3]["id"]},
        {"source": nodes[2]["id"], "target": nodes[3]["id"]},
    ] + [
        {"source": nodes[index]["id"], "target": nodes[index + 1]["id"]}
        for index in range(3, len(nodes) - 1)
    ]
    return data


def encoded(data):
    return json.dumps(data, ensure_ascii=False).encode()


def test_diamond_graph_creates_real_choice_and_merge():
    data = branched()
    result = build_editable_graph(encoded(data), "Ветвление")
    scenario = result.scenario
    choice = scenario.nodes[0]
    assert choice.kind == "choice"
    assert len(choice.options) == 2
    assert len({option.target for option in choice.options}) == 2
    assert scenario.nodes[-1].kind == "end"
    assert result.checked_positions()
    assert scenario.model_validate(scenario.model_dump())


def test_branch_preview_matches_imported_scenario_without_persistence():
    data = branched()
    expected = build_editable_graph(encoded(data), "Ветвление")
    response = client.post(
        "/api/v1/blueprint/import-graph/preview",
        data={"name": "Ветвление"},
        files={"plan_file": ("blueprint.json", encoded(data), "application/json")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["saved"] is False
    assert result["deployable"] is False
    assert result["summary"]["choices"] == 1
    assert result["scenario"] == expected.scenario.model_dump()


def test_cycle_is_rejected_before_save():
    data = branched()
    nodes = data["architecture"]["nodes"]
    data["architecture"]["links"].append({
        "source": nodes[-1]["id"], "target": nodes[0]["id"],
    })
    with pytest.raises(ValueError):
        build_editable_graph(encoded(data), "Цикл")


def test_unconfirmed_import_still_rejected():
    data = branched()
    response = client.post(
        "/api/v1/blueprint/import-graph",
        data={"name": "Ветвление", "confirm_placeholders": "false"},
        files={"plan_file": ("blueprint.json", encoded(data), "application/json")},
    )
    assert response.status_code == 422
