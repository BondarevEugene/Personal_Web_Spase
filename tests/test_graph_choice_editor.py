"""Graph Studio choice editor integration contracts.

The imported Blueprint branches must remain editable, valid and simulatable.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.simple_builder import SimulationRequest, simulate_scenario
from omni_site.blueprint_graph_import import build_editable_graph
from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from server import app

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def branched_plan():
    spec = compile_specification(
        sector="telegram", team="growth", process="manual", priority="control",
    )
    sections = build_project_plan(spec)
    data = {
        "schema": "omnifactory.blueprint.plan.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "architecture": sections.architecture,
        "milestones": sections.milestones,
        "verification": sections.verification,
        "risks": sections.risks,
    }
    nodes = data["architecture"]["nodes"]
    data["architecture"]["links"] = [
        {"source": nodes[0]["id"], "target": nodes[1]["id"]},
        {"source": nodes[0]["id"], "target": nodes[2]["id"]},
        {"source": nodes[1]["id"], "target": nodes[3]["id"]},
        {"source": nodes[2]["id"], "target": nodes[3]["id"]},
        *(
            {"source": nodes[i]["id"], "target": nodes[i + 1]["id"]}
            for i in range(3, len(nodes) - 1)
        ),
    ]
    return json.dumps(data, ensure_ascii=False).encode()


def test_imported_choice_can_change_target_and_simulate():
    data = build_editable_graph(branched_plan(), "Editable workflow")
    choice = data.scenario.nodes[0]
    assert choice.kind == "choice"
    choice.options[0].target = choice.options[1].target
    scenario = data.scenario.model_validate(data.scenario.model_dump())
    result = simulate_scenario(SimulationRequest(
        scenario=scenario, choices={choice.id: 0},
    ))
    assert result["status"] in {"completed", "finished", "done"}


def test_editor_exposes_branch_controls_and_marks_dirty():
    js = (ROOT / "omni_site/static/graph_project_editor.js").read_text(
        encoding="utf-8",
    )
    assert 'className = "graph-choice-option"' in js
    assert '"Удалить кнопку "' in js
    assert 'addOption.disabled = node.options.length >= 8' in js
    assert 'option.target = select.value;' in js
    assert "markDirty();" in js
    response = CLIENT.get("/studio-assets/graph_project_workspace.css")
    assert response.status_code == 200
    assert ".graph-choice-option" in response.text
