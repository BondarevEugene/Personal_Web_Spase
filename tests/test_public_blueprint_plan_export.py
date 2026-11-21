"""Public JSON Blueprint export contract and cross-format consistency."""
import io
import json
import re
import zipfile

import pytest
from fastapi.testclient import TestClient

from server import app

CLIENT = TestClient(app)
DATA = {
    "sector": "crm",
    "team": "growth",
    "process": "manual",
    "priority": "control",
}


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_json_plan_matches_zip_and_is_not_deployable(sector):
    form = {**DATA, "sector": sector}
    response = CLIENT.post("/demo/blueprint/plan", data=form)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert re.fullmatch(
        r'attachment; filename="omnifactory-plan-[a-f0-9]{12}\.json"',
        response.headers["content-disposition"],
    )
    payload = response.json()
    assert payload["schema"] == "omnifactory.blueprint.plan.v1"
    assert payload["deployable"] is False
    assert payload["status"] == "draft"
    archive_response = CLIENT.post("/demo/blueprint/package", data=form)
    assert archive_response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        config = json.loads(archive.read("blueprint.json"))
        assert payload["revision"] == config["revision"]
        for name in ("architecture", "milestones", "verification", "risks"):
            assert payload[name] == json.loads(archive.read(name + ".json"))


def test_json_plan_is_deterministic_and_ignores_checkbox_order():
    form = {**DATA, "integration": ["telegram", "payments"]}
    reverse = {**DATA, "integration": ["payments", "telegram"]}
    a = CLIENT.post("/demo/blueprint/plan", data=form)
    b = CLIENT.post("/demo/blueprint/plan", data=reverse)
    assert a.status_code == b.status_code == 200
    assert a.content == b.content


@pytest.mark.parametrize("field", ["sector", "team", "process", "priority"])
def test_json_plan_rejects_invalid_options(field):
    response = CLIENT.post(
        "/demo/blueprint/plan", data={**DATA, field: "invalid"},
    )
    assert response.status_code == 422


def test_json_plan_rejects_duplicate_integrations_and_missing_inputs():
    response = CLIENT.post(
        "/demo/blueprint/plan",
        data={**DATA, "integration": ["telegram", "telegram"]},
    )
    assert response.status_code == 422
    missing = CLIENT.post("/demo/blueprint/plan", data={"sector": "crm"})
    assert missing.status_code == 422
    assert CLIENT.get("/demo/blueprint/plan").status_code == 405


def test_blueprint_page_exposes_json_export_without_javascript():
    response = CLIENT.post("/demo/blueprint", data=DATA)
    assert response.status_code == 200
    assert 'formaction="/demo/blueprint/plan"' in response.text
    assert "Экспорт плана (.json)" in response.text
