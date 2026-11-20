"""Production readiness gate: safe checks and migration health without DB writes."""
import json
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from portal.db import engine, session_factory
from portal.release_doctor import (
    EXPECTED_TABLES, REQUIRED_ASSETS, assess, assess_config, assess_database,
    assess_routes, main,
)

ROOT = Path(__file__).resolve().parents[1]


def valid_production_config():
    return {
        "OMNI_PORTAL_DATABASE_URL":
            "postgresql+psycopg2://example:secret@db.example.com/omni",
        "OMNI_PORTAL_MIGRATION_URL":
            "postgresql+psycopg2://example:secret@db.example.com/omni",
        "OMNI_PORTAL_CSRF_SECRET": "a" * 48,
        "OMNI_PORTAL_ALLOW_REGISTRATION": "0",
        "OMNI_PUBLIC_BASE_URL": "https://omni.example.com",
        "OMNIFACTORY_CORS_ORIGINS": "https://app.example.com",
    }


def names(result):
    return {item.name: item.status for item in result}


def test_production_config_requires_real_database_and_shared_csrf():
    ok = assess_config(production=True, env=valid_production_config())
    assert all(item.status == "pass" for item in ok), ok
    unsafe = valid_production_config()
    unsafe.update({
        "OMNI_PORTAL_DATABASE_URL": "sqlite:///portal_dev.sqlite3",
        "OMNI_PORTAL_MIGRATION_URL":
            "postgresql://name:password@ep-pooler.example.com/db",
        "OMNI_PORTAL_CSRF_SECRET": "short",
        "OMNI_PORTAL_ALLOW_REGISTRATION": "",
        "OMNI_PUBLIC_BASE_URL": "http://public.example.com",
        "OMNIFACTORY_CORS_ORIGINS": "*",
    })
    report = assess_config(production=True, env=unsafe)
    failed = {item.name for item in report if item.status == "fail"}
    assert failed >= {
        "portal_database", "direct_migration_url", "csrf_secret",
        "registration_policy", "https_external_url", "cors_policy",
        "migration_not_pooler",
    }
    output = json.dumps(assess(production=True, env=unsafe))
    assert "password@" not in output
    assert "secret@" not in output
    assert "portal_dev.sqlite3" not in output


def test_local_development_mode_does_not_force_neon():
    report = assess(production=False, database=False, env={})
    assert report["mode"] == "development"
    assert report["ready"] is True
    assert names(assess_config(production=False, env={}))["environment"] == "pass"


@pytest.mark.parametrize("bad_origins", [
    "*", "https://safe.test,*", "ftp://host.test",
    "https://user:password@host.test", "http://not-secure.test",
])
def test_production_rejects_unsafe_cors(bad_origins):
    conf = valid_production_config()
    conf["OMNIFACTORY_CORS_ORIGINS"] = bad_origins
    assert names(assess_config(production=True, env=conf))["cors_policy"] == "fail"


def test_required_workspace_assets_match_repository():
    assert len(REQUIRED_ASSETS) >= 10
    assert len(EXPECTED_TABLES) >= 10
    for asset in REQUIRED_ASSETS:
        assert (ROOT / asset).is_file(), asset
    assert names(assess_config(production=False, env={}))["workspace_assets"] == "pass"
    assert names(assess_config(production=False, env={}, root=ROOT / "missing"))[
        "workspace_assets"
    ] == "fail"


def test_read_only_database_probe_detects_current_migrations(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "readiness.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    try:
        before = assess_database()
        assert names(before)["database_connection"] == "pass"
        assert names(before)["migration_head"] == "fail"
        config = Config(str(ROOT / "portal_alembic.ini"))
        command.upgrade(config, "head")
        after = assess_database()
        assert names(after)["required_tables"] == "pass", after
        assert names(after)["migration_head"] == "pass", after
        assert names(after)["migration_graph"] == "pass", after
    finally:
        engine.cache_clear()
        session_factory.cache_clear()


def test_cli_returns_nonzero_for_unready_prod(monkeypatch, capsys):
    monkeypatch.setattr(os, "environ", {
        "OMNI_PORTAL_DATABASE_URL": "sqlite:///local.sqlite3",
    })
    monkeypatch.setattr("sys.argv", [
        "release_doctor", "--production", "--json",
    ])
    assert main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["ready"] is False
    assert result["failed"] > 0
    assert result["mode"] == "production"


def test_route_contract_includes_customer_delivery_and_graph_studio():
    result = assess_routes()
    assert names(result)["public_route_contract"] == "pass", result
    report = assess(production=False, database=False, routes=True, env={})
    assert report["ready"] is True
    assert report["failed"] == 0


def test_security_headers_on_private_pages_and_https():
    from server import app

    client = TestClient(app)
    response = client.get("/account/login")
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "strict-transport-security" not in response.headers
    health = client.get("/health")
    assert health.headers["x-content-type-options"] == "nosniff"

    secure_client = TestClient(app, base_url="https://testserver")
    secure_response = secure_client.get("/account/login")
    assert secure_response.status_code == 200
    assert secure_response.headers["strict-transport-security"] == "max-age=31536000"
