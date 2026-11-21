"""End-to-end Blueprint JSON import preview, without persistence."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from omni_site.blueprint_plan_import import PlanValidationError, validate_plan
from server import app

CLIENT = TestClient(app)
FORM = {"sector": "crm", "team": "growth", "process": "manual", "priority": "control"}


def plan_data(sector="crm"):
    spec = compile_specification(**{**FORM, "sector": sector})
    plan = build_project_plan(spec)
    return {
        "schema": "omnifactory.blueprint.plan.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "architecture": plan.architecture,
        "milestones": plan.milestones,
        "verification": plan.verification,
        "risks": plan.risks,
    }


def upload(data, content_type="application/json"):
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return CLIENT.post(
        "/demo/blueprint/preview",
        files={"plan_file": ("plan.json", payload, content_type)},
    )


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_preview_matches_generated_plan_without_creating_project(sector):
    response = upload(plan_data(sector))
    assert response.status_code == 200
    preview = response.json()
    assert preview["status"] == "validated_not_imported"
    assert preview["executable"] is False
    assert preview["components"] >= 4
    assert preview["milestones"] == 5
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(deployable=True),
    lambda p: p["architecture"].update(deployable=True),
    lambda p: p["architecture"]["integrations"].append(
        {"id": "external", "name": "API", "connected": True}
    ),
    lambda p: p["architecture"]["links"].append(
        {"source": "unknown", "target": "component-01"}
    ),
    lambda p: p["milestones"]["items"][0].update(depends_on=["unknown"]),
    lambda p: p["verification"]["checks"][0].update(result="passed"),
    lambda p: p["risks"]["items"][0].update(status="closed"),
    lambda p: p["architecture"].update(revision="000000000000"),
])
def test_preview_rejects_unsafe_or_inconsistent_plan(mutation):
    data = copy.deepcopy(plan_data())
    mutation(data)
    assert upload(data).status_code == 422


def test_preview_rejects_malformed_and_oversized_upload():
    response = CLIENT.post(
        "/demo/blueprint/preview",
        files={"plan_file": ("plan.json", b"not-json", "application/json")},
    )
    assert response.status_code == 422
    response = CLIENT.post(
        "/demo/blueprint/preview",
        files={"plan_file": ("plan.json", b"x" * 256001, "application/json")},
    )
    assert response.status_code == 422
    assert upload(plan_data(), "image/png").status_code == 415
    assert CLIENT.get("/demo/blueprint/preview").status_code == 405


def test_preview_is_deterministic_and_pure():
    payload = json.dumps(plan_data()).encode()
    assert validate_plan(payload) == validate_plan(payload)
    with pytest.raises(PlanValidationError):
        validate_plan(b"{}")
