"""Connector diagnostics must be safe, deterministic and owner-scoped."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import automation
from automation.connector_diagnostics import diagnose, operator_overview
from automation.engine import WorkflowDefinition


def definition(kind, config):
    return WorkflowDefinition.model_validate({
        "name": "Diagnostic scenario",
        "start": "start",
        "nodes": [
            {"id": "start", "kind": "trigger", "next": "external"},
            {"id": "external", "kind": kind, "config": config, "next": "finish"},
            {"id": "finish", "kind": "end"},
        ],
    })


def test_no_external_calls_and_no_secrets_in_diagnostics(monkeypatch):
    monkeypatch.delenv("OMNI_AUTOMATION_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("OMNI_CREDENTIAL_GOOGLE", "top-secret-value")
    result = diagnose(definition("google_docs", {
        "action": "create", "credential": "OMNI_CREDENTIAL_GOOGLE",
    }))
    assert result["network_calls"] == 0
    assert result["nodes"][0]["status"] == "configuration_blocked"
    assert "platform_live_disabled" in result["nodes"][0]["reasons"]
    assert "top-secret-value" not in str(result)
    assert "OMNI_CREDENTIAL_GOOGLE" not in str(result)


def test_config_ready_does_not_claim_provider_permissions(monkeypatch):
    monkeypatch.setenv("OMNI_AUTOMATION_LIVE_ENABLED", "1")
    monkeypatch.setenv("OMNI_CREDENTIAL_GOOGLE", "secret")
    result = diagnose(definition("google_docs", {
        "action": "create", "credential": "OMNI_CREDENTIAL_GOOGLE",
    }))
    assert result["ready"] == 1
    assert result["external_permissions_verified"] is False
    assert result["nodes"][0]["network_tested"] is False


def test_http_requires_allowlist_and_egress_proxy(monkeypatch):
    monkeypatch.setenv("OMNI_AUTOMATION_LIVE_ENABLED", "1")
    monkeypatch.setenv("OMNI_AUTOMATION_HTTP_LIVE_ENABLED", "1")
    monkeypatch.delenv("OMNI_AUTOMATION_EGRESS_PROXY", raising=False)
    monkeypatch.setenv("OMNI_AUTOMATION_ALLOWED_HOSTS", "example.com")
    result = diagnose(definition("http", {
        "url": "https://example.com/path", "method": "GET",
    }))
    assert "egress_proxy_missing" in result["nodes"][0]["reasons"]


def test_operator_overview_is_not_network_probe():
    result = operator_overview()
    assert result["network_calls"] == 0
    assert len(result["connectors"]) == 5
    assert all(row["permissions_verified"] is False for row in result["connectors"])


def test_diagnostic_endpoints_require_authentication(monkeypatch):
    class Context:
        def __enter__(self):
            return object()

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(automation, "session_factory", lambda: lambda: Context())
    app = FastAPI()
    app.include_router(automation.router)
    client = TestClient(app)
    assert client.get("/api/v1/automation/connectors/diagnostics").status_code == 401
    assert client.get(
        "/api/v1/automation/workflows/00000000-0000-0000-0000-000000000001/connectors/diagnostics"
    ).status_code == 401
