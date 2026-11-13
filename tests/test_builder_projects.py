"""Account-backed builder drafts must remain private and CSRF protected."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from portal.db import engine, session_factory
from server import app

SCENARIO = {
    "name": "Welcome bot",
    "start": "hello",
    "nodes": [
        {"id": "hello", "kind": "message", "text": "Привет!", "next": "done"},
        {"id": "done", "kind": "end", "text": "До встречи!"},
    ],
}
BASE = "/api/v1/builder/projects"


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "builder_cloud.sqlite3").as_posix()
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


def register(username, address):
    c = TestClient(app)
    result = c.get("/account/register")
    assert result.status_code == 200
    token = c.cookies.get("omni_portal_csrf")
    result = c.post("/account/register", data={
        "csrf_token": token,
        "username": username,
        "email": address,
        "display_name": "Test Builder",
        "organization": username + " org",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    }, follow_redirects=False)
    assert result.status_code == 303, result.text
    return c


def csrf(c):
    response = c.get(BASE + "/csrf")
    assert response.status_code == 200, response.text
    return {"X-Omni-CSRF": response.json()["csrf_token"]}


def test_unauthenticated_project_api_denies_access(db_ready):
    c = TestClient(app)
    assert c.get(BASE).status_code == 401
    assert c.get(BASE + "/csrf").status_code == 401
    assert c.post(BASE, json={"scenario": SCENARIO}).status_code == 401


def test_create_list_open_update_delete_and_csrf(db_ready):
    c = register("build_owner", "owner@builder.test")
    assert c.get(BASE).json() == {"projects": []}
    body = {"scenario": SCENARIO, "positions": {"hello": {"x": 50, "y": 60}}}
    assert c.post(BASE, json=body).status_code == 403
    created = c.post(BASE, headers=csrf(c), json=body)
    assert created.status_code == 201, created.text
    id = created.json()["id"]
    assert created.json()["name"] == "Welcome bot"
    assert c.get(BASE).json()["projects"][0]["id"] == id
    saved = c.get(BASE + "/" + id)
    assert saved.status_code == 200
    assert saved.json()["scenario"]["name"] == SCENARIO["name"]
    assert saved.json()["scenario"]["start"] == SCENARIO["start"]
    assert [node["id"] for node in saved.json()["scenario"]["nodes"]] == ["hello", "done"]
    assert saved.json()["scenario"]["nodes"][0]["text"] == "Привет!"
    assert saved.json()["positions"]["hello"] == {"x": 50.0, "y": 60.0}


    modified = {"scenario": {**SCENARIO, "name": "Updated bot"},
                "positions": {"done": {"x": 70, "y": 100}}}
    assert c.put(BASE + "/" + id, json=modified).status_code == 403
    updated = c.put(BASE + "/" + id, headers=csrf(c), json=modified)
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Updated bot"
    assert c.delete(BASE + "/" + id).status_code == 403
    deleted = c.delete(BASE + "/" + id, headers=csrf(c))
    assert deleted.status_code == 204
    assert c.get(BASE + "/" + id).status_code == 404


def test_draft_is_isolated_between_customers(db_ready):
    owner = register("builder_a", "a@builder.test")
    other = register("builder_b", "b@builder.test")
    created = owner.post(BASE, headers=csrf(owner), json={"scenario": SCENARIO})
    assert created.status_code == 201, created.text
    id = created.json()["id"]
    assert other.get(BASE).json() == {"projects": []}
    assert other.get(BASE + "/" + id).status_code == 404
    assert other.put(BASE + "/" + id, headers=csrf(other),
                     json={"scenario": SCENARIO}).status_code == 404
    assert other.delete(BASE + "/" + id, headers=csrf(other)).status_code == 404
    assert owner.get(BASE + "/" + id).status_code == 200


def test_invalid_graph_and_layout_cannot_be_saved(db_ready):
    c = register("builder_valid", "valid@builder.test")
    token = csrf(c)
    broken = {"scenario": {**SCENARIO, "nodes": [
        {**SCENARIO["nodes"][0], "next": "missing"}, SCENARIO["nodes"][1]
    ]}}
    assert c.post(BASE, headers=token, json=broken).status_code == 422
    assert c.post(BASE, headers=token, json={
        "scenario": SCENARIO, "positions": {"unknown": {"x": 1, "y": 2}}
    }).status_code == 422
