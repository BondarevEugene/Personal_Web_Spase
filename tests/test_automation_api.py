"""Auth, migrations, webhook isolation, idempotent runs, revision control."""
import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from portal.db import engine, session_factory
from server import app

BASE = "/api/v1/automation"
DEFINITION = {
    "name": "Acquisition flow", "start": "trigger",
    "nodes": [
        {"id": "trigger", "kind": "trigger", "next": "assign"},
        {"id": "assign", "kind": "set", "next": "finish",
         "config": {"variable": "message", "value": "Hello {{customer}}"}},
        {"id": "finish", "kind": "end"},
    ],
}


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "automation.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.delenv("OMNI_AUTOMATION_LIVE_ENABLED", raising=False)
    engine.cache_clear()
    session_factory.cache_clear()
    cfg = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(cfg, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(username):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    response = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": username, "email": username + "@example.test",
        "display_name": "Workflow tester", "organization": username + " org",
        "password": "Strong-Test-Password-2026",
        "password_repeat": "Strong-Test-Password-2026",
    })
    assert response.status_code == 303, response.text
    return client


def csrf(client):
    response = client.get("/api/v1/builder/projects/csrf")
    assert response.status_code == 200
    return {"X-Omni-CSRF": response.json()["csrf_token"]}


def test_public_catalog_and_authentication_boundary(db_ready):
    client = TestClient(app)
    result = client.get(BASE + "/catalog")
    assert result.status_code == 200
    assert "google_docs" in result.json()["supported"]
    assert client.get(BASE + "/workflows").status_code == 401
    assert client.post(BASE + "/workflows", json={"definition": DEFINITION}).status_code == 401


def test_workflow_crud_revision_conflicts_and_tenant_isolation(db_ready):
    one = register("workflow_one")
    two = register("workflow_two")
    created = one.post(BASE + "/workflows", headers=csrf(one),
                       json={"definition": DEFINITION})
    assert created.status_code == 201, created.text
    item = created.json()
    id = item["id"]
    assert item["revision"] == 1
    assert one.get(BASE + "/workflows/" + id).status_code == 200
    assert two.get(BASE + "/workflows/" + id).status_code == 404
    assert two.get(BASE + "/workflows").json() == {"workflows": []}
    assert one.put(BASE + "/workflows/" + id, json={
        "definition": DEFINITION, "revision": 1}).status_code == 403
    changed = one.put(BASE + "/workflows/" + id, headers=csrf(one), json={
        "definition": DEFINITION, "revision": 1})
    assert changed.status_code == 200, changed.text
    assert changed.json()["revision"] == 2
    stale = one.put(BASE + "/workflows/" + id, headers=csrf(one), json={
        "definition": DEFINITION, "revision": 1})
    assert stale.status_code == 409


def test_durable_run_trace_and_idempotency(db_ready):
    c = register("workflow_runner")
    created = c.post(BASE + "/workflows", headers=csrf(c),
                     json={"definition": DEFINITION})
    assert created.status_code == 201, created.text
    workflow_id = created.json()["id"]
    url = BASE + "/workflows/" + workflow_id + "/runs"
    token = csrf(c)
    assert c.post(url, json={"input": {"customer": "Alex"}}).status_code == 403
    assert c.post(url, headers=token, json={
        "input": {"customer": "Alex"}, "live": True}).status_code == 422
    headers = {**csrf(c), "Idempotency-Key": "workflow-test-run-001"}
    first = c.post(url, headers=headers, json={"input": {"customer": "Alex"}})
    assert first.status_code == 201, first.text
    run_id = first.json()["id"]
    assert first.json()["status"] == "completed"
    second = c.post(url, headers=headers, json={"input": {"customer": "Alex"}})
    assert second.status_code == 201, second.text
    assert second.json()["id"] == run_id
    listing = c.get(url)
    assert listing.status_code == 200
    assert len(listing.json()["runs"]) == 1
    assert [x["node"] for x in listing.json()["runs"][0]["trace"]] == [
        "trigger", "assign", "finish"]
    assert c.delete(BASE + "/workflows/" + workflow_id,
                    headers=csrf(c)).status_code == 409


def test_webhook_token_issued_once_and_only_dry_runs(db_ready):
    c = register("workflow_hook")
    created = c.post(BASE + "/workflows", headers=csrf(c), json={
        "definition": DEFINITION})
    id = created.json()["id"]
    enable = c.post(BASE + "/workflows/" + id + "/webhook", headers=csrf(c))
    assert enable.status_code == 201, enable.text
    token = enable.json()["token"]
    hook_url = "/hooks/automation/" + id
    assert c.post(hook_url, json={"customer": "Ada"}).status_code == 404
    signed = c.post(hook_url, headers={"X-Omni-Webhook-Token": token},
                    json={"customer": "Ada"})
    assert signed.status_code == 202, signed.text
    assert signed.json()["status"] == "completed"
    assert c.get(BASE + "/workflows/" + id + "/runs").json()["runs"][0]["mode"] == "dry_run"
    assert c.delete(BASE + "/workflows/" + id + "/webhook", headers=csrf(c)).status_code == 204
    assert c.post(hook_url, headers={"X-Omni-Webhook-Token": token},
                  json={"customer": "Ada"}).status_code == 404
