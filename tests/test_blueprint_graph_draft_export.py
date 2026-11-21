"""Graph draft export is deterministic, non-executable and mobile accessible."""
import json

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_graph_draft import graph_draft
from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from server import app

CLIENT = TestClient(app)


def plan(sector):
    spec = compile_specification(
        sector=sector, team="growth", process="manual", priority="control",
    )
    parts = build_project_plan(spec)
    return {
        "schema": "omnifactory.blueprint.plan.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "architecture": parts.architecture,
        "milestones": parts.milestones,
        "verification": parts.verification,
        "risks": parts.risks,
    }


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_graph_draft_export_matches_blueprint_and_never_executes(sector):
    data = json.dumps(plan(sector), ensure_ascii=False).encode()
    a = graph_draft(data)
    b = graph_draft(data)
    assert a == b
    assert a["schema"] == "omnifactory.graph.draft.v1"
    assert a["status"] == "design_only"
    assert a["executable"] is False
    assert a["requires_review"] is True
    assert all(node["type"] == "note" for node in a["nodes"])
    assert all(edge["executable"] is False for edge in a["edges"])
    response = CLIENT.post(
        "/demo/blueprint/graph-draft",
        files={"plan_file": ("plan.json", data, "application/json")},
    )
    assert response.status_code == 200
    assert response.json() == a
    assert response.headers["cache-control"] == "no-store"
    assert "attachment;" in response.headers["content-disposition"]


def test_graph_draft_rejects_malformed_or_executable_input():
    data = plan("crm")
    data["deployable"] = True
    response = CLIENT.post(
        "/demo/blueprint/graph-draft",
        files={"plan_file": ("plan.json", json.dumps(data), "application/json")},
    )
    assert response.status_code == 422
    assert CLIENT.get("/demo/blueprint/graph-draft").status_code == 405


def test_graph_draft_form_is_accessible():
    response = CLIENT.get("/demo/blueprint")
    assert response.status_code == 200
    assert 'action="/demo/blueprint/graph-draft"' in response.text
    assert 'id="blueprint-graph-file"' in response.text
