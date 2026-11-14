"""Runtime safety: owner-only preflight, bounded scenario and strict webhook auth."""
import base64
import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from portal.db import engine, session_factory
from runtime.telegram.scenario import read_scenario
from server import app


SCENARIO = {
    "name": "Safe Bot", "start": "start",
    "nodes": [
        {"id": "start", "kind": "input", "text": "Name?", "variable": "name", "next": "condition"},
        {"id": "condition", "kind": "condition", "variable": "name",
         "operator": "not_empty", "value": "", "true_target": "message",
         "false_target": "end"},
        {"id": "message", "kind": "message", "text": "Hi, {{name}}", "next": "end"},
        {"id": "end", "kind": "end", "text": "Done"},
    ],
}


def encoded(value):
    return base64.b64encode(json.dumps(value).encode()).decode()


def test_scenario_validation_accepts_real_logic_nodes():
    scenario = read_scenario(encoded(SCENARIO))
    assert len(scenario["nodes"]) == 4


@pytest.mark.parametrize("value", [
    {},
    {"start": "missing", "nodes": SCENARIO["nodes"]},
    {"start": "start", "nodes": SCENARIO["nodes"][:1]},
    {"start": "start", "nodes": SCENARIO["nodes"] + [SCENARIO["nodes"][0]]},
    {"start": "start", "nodes": [{"id": "start", "kind": "http", "next": "start"}]},
    {"start": "start", "nodes": [{"id": "start", "kind": "set_variable",
                                  "variable": "__bad", "next": "start"}]},
])
def test_scenario_rejects_invalid_graph(value):
    with pytest.raises(ValueError):
        read_scenario(encoded(value))


def test_scenario_rejects_large_payload():
    with pytest.raises(ValueError):
        read_scenario(encoded(SCENARIO) + "A" * 300_001)


@pytest.fixture
def portal_db(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "runtime.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    cfg = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(cfg, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(username):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    r = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username,
        "email": username + "@test.example",
        "display_name": "Runtime Tester", "organization": username + " org",
        "password": "Strong-Test-Password-2026",
        "password_repeat": "Strong-Test-Password-2026",
    })
    assert r.status_code == 303, r.text
    return c


def csrf(c):
    r = c.get("/api/v1/builder/projects/csrf")
    assert r.status_code == 200, r.text
    return {"X-Omni-CSRF": r.json()["csrf_token"]}


def test_runtime_preflight_owner_only(portal_db):
    owner = register("runtime_owner")
    outsider = register("runtime_other")
    created = owner.post("/api/v1/builder/projects", headers=csrf(owner),
                         json={"scenario": SCENARIO})
    assert created.status_code == 201, created.text
    bot_id = created.json()["id"]
    url = "/api/v1/cloud/runtime/preflight/" + bot_id
    assert TestClient(app).get(url).status_code == 401
    assert outsider.get(url).status_code == 404
    result = owner.get(url)
    assert result.status_code == 200, result.text
    info = result.json()
    assert info["scenario_compatible"] is True
    assert "condition" in info["node_types"]
    assert info["production_ready"] is False
    assert info["verified_telegram_delivery"] is False
    assert info["scenario_sha256"]
    assert "BOT_TOKEN" not in result.text
    assert owner.get("/api/v1/cloud/runtime/capabilities").json()["live_railway_deploy_enabled"] is False


def test_real_webhook_runtime_secret(monkeypatch):
    pytest.importorskip("aiogram")
    import sys
    from importlib import import_module
    # Runtime container imports the local scenario validator from its working directory.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime/telegram"))
    try:
        runtime = import_module("runtime.telegram.app")
        bot = runtime.Bot("123456789:" + "A" * 35)
        app_instance = runtime.build_runtime(read_scenario(encoded(SCENARIO)),
                                             bot, "trusted-webhook-secret-0123456789")
        c = TestClient(app_instance)
        assert c.get("/health").json()["telegram_delivery_verified"] is False
        assert c.post("/telegram/webhook", json={}).status_code == 403
        assert c.post("/telegram/webhook",
                      headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
                      json={}).status_code == 403
        assert c.post("/telegram/webhook",
                      headers={"X-Telegram-Bot-Api-Secret-Token": "trusted-webhook-secret-0123456789"},
                      content=b"not-json").status_code == 400
    finally:
        sys.path.remove(str(Path(__file__).resolve().parents[1] / "runtime/telegram"))
