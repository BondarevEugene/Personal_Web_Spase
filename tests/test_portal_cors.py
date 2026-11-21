"""Regression tests for portal CORS policy."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.middleware import cors_origins_from_env, setup_middleware


def _client():
    app = FastAPI()
    setup_middleware(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(app)


def test_same_origin_default_has_no_cross_origin_credential_access(monkeypatch):
    monkeypatch.delenv("OMNIFACTORY_CORS_ORIGINS", raising=False)
    with _client() as client:
        response = client.get("/ping", headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_explicit_origin_allows_credentials(monkeypatch):
    monkeypatch.setenv("OMNIFACTORY_CORS_ORIGINS", "https://studio.example")
    with _client() as client:
        trusted = client.options("/ping", headers={
            "Origin": "https://studio.example",
            "Access-Control-Request-Method": "GET",
        })
        untrusted = client.options("/ping", headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        })
    assert trusted.headers["access-control-allow-origin"] == "https://studio.example"
    assert trusted.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in untrusted.headers


def test_wildcard_rejected(monkeypatch):
    monkeypatch.setenv("OMNIFACTORY_CORS_ORIGINS", "*")
    with pytest.raises(ValueError, match="explicit origins"):
        cors_origins_from_env()


def test_explicit_origins_trimmed_and_deduplicated(monkeypatch):
    monkeypatch.setenv(
        "OMNIFACTORY_CORS_ORIGINS",
        " https://studio.example/,https://studio.example, http://localhost:3000 ",
    )
    assert cors_origins_from_env() == ["https://studio.example", "http://localhost:3000"]
