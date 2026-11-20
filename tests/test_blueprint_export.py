"""Portable Blueprint contract and privacy regressions."""
import pytest
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)
URL = "/api/v1/blueprint/export"
BASE = {"sector": "crm", "team": "growth", "process": "manual",
        "priority": "control", "integrations": []}


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation"])
def test_portable_export_for_each_product(sector):
    response = client.post(URL, json={**BASE, "sector": sector})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["schema"] == "omnifactory.blueprint.v1"
    assert data["kind"] == "planning_brief"
    assert data["saved"] is False
    assert data["deployable"] is False
    assert data["input"]["sector"] == sector
    assert len(data["blueprint"]["stages"]) >= 5
    assert response.headers["cache-control"] == "no-store"
    assert "noindex" in response.headers["x-robots-tag"]


@pytest.mark.parametrize("patch", [
    {"sector": "unknown"}, {"team": "admin"}, {"extra": "secret"},
    {"integrations": ["unknown"]}, {"integrations": ["api"] * 5},
])
def test_invalid_export_is_rejected(patch):
    assert client.post(URL, json={**BASE, **patch}).status_code == 422


def test_repeatable_export_does_not_claim_persistence():
    first = client.post(URL, json=BASE)
    second = client.post(URL, json=BASE)
    assert first.json() == second.json()
    assert first.json()["saved"] is False
