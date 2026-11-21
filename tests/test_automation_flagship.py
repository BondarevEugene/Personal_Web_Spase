"""Automation Flagship: real bounded dry-run, public routes and catalogue."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from automation.engine import WorkflowDefinition
from omni_site.automation_flagship import (
    BY_SLUG,
    INTEGRATIONS,
    STATUS_LABELS,
    TEMPLATES,
    preview,
    template_definition,
)
from omni_site.automation_flagship_routes import router


def test_all_templates_are_valid_graphs_and_execute_without_side_effects():
    assert len(TEMPLATES) == 3
    assert len(BY_SLUG) == len(TEMPLATES)
    for item in TEMPLATES:
        definition = template_definition(item.slug)
        assert isinstance(definition, WorkflowDefinition)
        result = preview(item.slug)
        assert result["mode"] == "dry_run"
        assert result["external_calls_executed"] is False
        assert result["trace"]
        assert result["status"] in {"completed", "awaiting_approval"}


def test_preview_exposes_real_conditional_branch_and_manual_approval():
    lead = preview("lead-qualification")
    assert lead["status"] == "awaiting_approval"
    assert lead["variables"]["segment"] == "priority"
    assert any(step.get("outcome") == "true" for step in lead["trace"])
    assert any(step.get("outcome") == "awaiting_approval" for step in lead["trace"])


def test_document_preview_routes_to_finance_queue():
    result = preview("document-routing")
    assert result["status"] == "completed"
    assert result["variables"]["queue"] == "finance_review"


def test_http_preview_does_not_perform_network_requests(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("External HTTP request attempted")

    import httpx

    monkeypatch.setattr(httpx, "Client", deny)
    result = preview("integration-preview")
    assert result["status"] == "completed"
    assert result["variables"]["api_preview"]["mode"] == "dry_run"


def test_catalogue_labels_distinguish_live_gated_and_not_implemented():
    assert len({integration.slug for integration in INTEGRATIONS}) == len(INTEGRATIONS)
    assert all(integration.status in STATUS_LABELS for integration in INTEGRATIONS)
    assert any(integration.status == "planned" for integration in INTEGRATIONS)
    assert any(integration.status == "gated_live" for integration in INTEGRATIONS)


def test_public_api_download_and_preview_contract():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    page = client.get("/integrations")
    assert page.status_code == 200
    assert "Automation" in page.text
    download = client.get("/integrations/templates/document-routing")
    assert download.status_code == 200
    assert download.json()["start"] == "incoming"
    assert "attachment;" in download.headers["content-disposition"]
    response = client.post("/integrations/preview/document-routing")
    assert response.status_code == 200
    assert response.json()["external_calls_executed"] is False
    assert client.post("/integrations/preview/not-found").status_code == 404
    assert client.get("/integrations/templates/not-found").status_code == 404
