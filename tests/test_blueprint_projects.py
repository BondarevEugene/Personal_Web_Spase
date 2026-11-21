"""Blueprint handoff produces a valid editable and exportable Telegram graph."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from omni_site.blueprint_projects import BlueprintProjectInput, build_telegram_graph
from server import app

client = TestClient(app)
URL = "/api/v1/blueprint/projects"
BASE = {
    "blueprint": {
        "sector": "telegram",
        "team": "growth",
        "process": "manual",
        "priority": "control",
        "integrations": ["telegram"],
    },
    "name": "Telegram заявки",
}


def test_graph_is_complete_reachable_and_serializable():
    data = build_telegram_graph(BlueprintProjectInput.model_validate(BASE))
    nodes = {node.id: node for node in data.scenario.nodes}
    assert len(nodes) == 6
    assert data.scenario.start == "welcome"
    assert nodes["choose"].options[0].target == "request"
    assert nodes["request"].next == "received"
    assert nodes["received"].next == "finish"
    assert "{{request_text}}" in nodes["received"].text
    assert set(data.positions) == set(nodes)
    assert data.checked_positions()
    assert data.scenario.model_validate(data.scenario.model_dump())


@pytest.mark.parametrize("sector", ["crm", "automation"])
def test_non_telegram_blueprints_are_not_falsely_deployable(sector):
    payload = BlueprintProjectInput.model_validate({
        **BASE, "blueprint": {**BASE["blueprint"], "sector": sector},
    })
    with pytest.raises(HTTPException) as error:
        build_telegram_graph(payload)
    assert error.value.status_code == 422


def test_anonymous_cannot_create_saved_project():
    response = client.post(URL, json=BASE)
    assert response.status_code == 401


def test_invalid_integration_is_rejected():
    response = client.post(URL, json={
        **BASE, "blueprint": {**BASE["blueprint"], "integrations": ["unknown"]},
    })
    assert response.status_code == 422
