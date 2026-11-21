"""Blueprint handoff must require login, CSRF and validated product choices."""
from fastapi.testclient import TestClient

from server import app

CLIENT = TestClient(app)
URL = "/api/v1/blueprint/handoff"
GOOD = {
    "title": "Blueprint · CRM и клиентские процессы",
    "blueprint": {
        "sector": "crm", "team": "growth", "process": "manual",
        "priority": "control", "integrations": ["database"],
    },
}


def test_anonymous_handoff_cannot_create_customer_project():
    response = CLIENT.post(URL, json=GOOD)
    assert response.status_code == 401


def test_handoff_rejects_invalid_product_choices_before_database_write():
    for field in ("sector", "team", "process", "priority"):
        payload = {
            **GOOD,
            "blueprint": {**GOOD["blueprint"], field: "invalid"},
        }
        assert CLIENT.post(URL, json=payload).status_code == 422


def test_handoff_rejects_duplicates_and_unknown_integrations():
    for integrations in (["database", "database"], ["invalid"]):
        payload = {
            **GOOD,
            "blueprint": {**GOOD["blueprint"], "integrations": integrations},
        }
        assert CLIENT.post(URL, json=payload).status_code == 422


def test_handoff_rejects_unbounded_title_and_extra_fields():
    assert CLIENT.post(URL, json={**GOOD, "title": "x"}).status_code == 422
    assert CLIENT.post(URL, json={**GOOD, "title": "x" * 161}).status_code == 422
    assert CLIENT.post(URL, json={**GOOD, "secret": "oops"}).status_code == 422


def test_public_form_offers_explicit_handoff_and_original_downloads():
    html = CLIENT.post("/demo/blueprint", data={
        "sector": "crm", "team": "growth",
        "process": "manual", "priority": "control",
    }).text
    assert 'id="blueprint-handoff"' in html
    assert 'id="blueprint-handoff-status"' in html
    assert "/studio-assets/blueprint_handoff.js" in html
    assert 'formaction="/demo/blueprint/package"' in html
    assert 'formaction="/demo/blueprint/specification"' in html
    js = CLIENT.get("/studio-assets/blueprint_handoff.js")
    assert js.status_code == 200
    assert '"/api/v1/blueprint/handoff"' in js.text
    assert '"/api/v1/builder/projects/csrf"' in js.text
