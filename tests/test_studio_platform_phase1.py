"""Non-destructive route regression tests for Studio/Platform Phase 1.

Run: python -m pytest -q tests/test_studio_platform_phase1.py
The TestClient is intentionally used without entering lifespan, so tests do not
create tables or contact a real database.
"""
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)

VALID_LEAD = {
    "name": "Тестовый клиент",
    "contact": "@test_contact",
    "topic": "CRM / управление бизнесом",
    "message": "Нужна CRM и интеграция с Telegram для отдела продаж.",
}


def test_public_studio_keeps_design_and_has_platform_entry():
    response = client.get("/studio")
    assert response.status_code == 200
    assert 'href="/studio-assets/site.css?v=3"' in response.text
    assert 'class="platform-link" href="/"' in response.text
    assert "Платформа OmniFactory" in response.text


def test_platform_links_back_to_studio_and_existing_builder():
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/studio"' in response.text
    assert 'href="/architect"' in response.text


def test_repaired_builder_ui_and_static_assets_are_accessible():
    response = client.get("/builder_pro_final.html")
    assert response.status_code == 200
    assert "Graph Studio v2" in response.text
    assert "/studio-assets/graph_studio.js?v=8" in response.text
    script = client.get("/studio-assets/graph_studio.js")
    assert script.status_code == 200
    assert "/api/v1/builder/simple" in script.text


def test_studio_assets_are_served():
    response = client.get("/studio-assets/site.css")
    assert response.status_code == 200
    assert ".platform-link" in response.text


def test_studio_lead_endpoint_is_registered():
    assert "/studio/api/lead" in app.openapi()["paths"]


def test_studio_lead_invalid_payload_returns_422():
    response = client.post("/studio/api/lead", json={"name": "A"})
    assert response.status_code == 422


def test_studio_lead_requires_telegram_configuration(monkeypatch):
    monkeypatch.delenv("OMNI_STUDIO_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OMNI_STUDIO_CHAT_ID", raising=False)
    response = client.post("/studio/api/lead", json=VALID_LEAD)
    assert response.status_code == 503
    assert response.json()["detail"] == "Telegram lead delivery not configured"


def test_studio_honeypot_does_not_send_telegram_request(monkeypatch):
    monkeypatch.delenv("OMNI_STUDIO_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OMNI_STUDIO_CHAT_ID", raising=False)
    response = client.post("/studio/api/lead", json={**VALID_LEAD, "website": "spam.example"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}
