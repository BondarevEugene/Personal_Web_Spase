"""Full Blueprint -> project -> edit -> reopen -> ownership -> delete regression.

Exercises real HTTP routes, CSRF, Alembic migrations and SQLite persistence.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from portal.db import engine, session_factory
from server import app

PROJECTS = "/api/v1/builder/projects"
BLUEPRINT = "/api/v1/blueprint/projects"
INPUT = {
    "name": "Telegram workflow E2E",
    "blueprint": {
        "sector": "telegram",
        "team": "growth",
        "process": "manual",
        "priority": "control",
        "integrations": ["telegram", "database"],
    },
}


@pytest.fixture
def migrated_database(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "blueprint_e2e.sqlite3").as_posix()
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


def register(username: str) -> TestClient:
    client = TestClient(app)
    response = client.get("/account/register")
    assert response.status_code == 200
    token = client.cookies["omni_portal_csrf"]
    response = client.post(
        "/account/register",
        data={
            "csrf_token": token,
            "username": username,
            "email": username + "@blueprint.test",
            "display_name": "Blueprint E2E",
            "organization": username + " organization",
            "password": "Strong-Password-2026",
            "password_repeat": "Strong-Password-2026",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    return client


def csrf(client: TestClient) -> dict[str, str]:
    response = client.get(PROJECTS + "/csrf")
    assert response.status_code == 200, response.text
    return {"X-Omni-CSRF": response.json()["csrf_token"]}


def test_complete_blueprint_project_lifecycle(migrated_database):
    owner = register("blueprint_owner")
    stranger = register("blueprint_stranger")

    assert owner.post(BLUEPRINT, json=INPUT).status_code == 403
    response = owner.post(BLUEPRINT, headers=csrf(owner), json=INPUT)
    assert response.status_code == 201, response.text
    identifier = response.json()["id"]

    saved = owner.get(PROJECTS + "/" + identifier)
    assert saved.status_code == 200
    document = saved.json()
    assert document["scenario"]["name"] == INPUT["name"]
    assert len(document["scenario"]["nodes"]) == 6
    assert document["scenario"]["start"] == "welcome"
    assert set(document["positions"]) == {
        node["id"] for node in document["scenario"]["nodes"]
    }

    page = owner.get("/account/graph-project/" + identifier)
    assert page.status_code == 200
    assert 'id="graph-editor"' in page.text
    assert 'data-project-id="' + identifier + '"' in page.text
    assert page.headers["cache-control"] == "no-store"
    assert stranger.get("/account/graph-project/" + identifier).status_code == 404
    assert stranger.get(PROJECTS + "/" + identifier).status_code == 404

    updated = document["scenario"]
    updated["name"] = "Edited workflow"
    updated["nodes"][0]["text"] = "Новый приветственный текст"
    modified = owner.put(
        PROJECTS + "/" + identifier,
        headers=csrf(owner),
        json={
            "scenario": updated,
            "positions": document["positions"],
            "groups": document["groups"],
        },
    )
    assert modified.status_code == 200, modified.text
    reopened = owner.get(PROJECTS + "/" + identifier)
    assert reopened.json()["scenario"]["name"] == "Edited workflow"
    assert reopened.json()["scenario"]["nodes"][0]["text"] == (
        "Новый приветственный текст"
    )
    assert reopened.json()["positions"] == document["positions"]

    invalid = {**updated, "start": "nonexistent"}
    assert owner.put(
        PROJECTS + "/" + identifier,
        headers=csrf(owner),
        json={"scenario": invalid},
    ).status_code == 422
    assert owner.get(PROJECTS + "/" + identifier).json()["scenario"]["start"] == "welcome"

    assert stranger.put(
        PROJECTS + "/" + identifier,
        headers=csrf(stranger),
        json={"scenario": updated},
    ).status_code == 404
    assert stranger.delete(
        PROJECTS + "/" + identifier,
        headers=csrf(stranger),
    ).status_code == 404

    assert owner.delete(PROJECTS + "/" + identifier).status_code == 403
    assert owner.delete(
        PROJECTS + "/" + identifier, headers=csrf(owner)
    ).status_code == 204
    assert owner.get(PROJECTS + "/" + identifier).status_code == 404


@pytest.mark.parametrize("sector", ["crm", "automation"])
def test_unsupported_blueprint_never_creates_project(migrated_database, sector):
    client = register("reject_" + sector)
    response = client.post(
        BLUEPRINT,
        headers=csrf(client),
        json={**INPUT, "blueprint": {**INPUT["blueprint"], "sector": sector}},
    )
    assert response.status_code == 422
    assert client.get(PROJECTS).json() == {"projects": []}


def test_anonymous_access_and_invalid_uuid(migrated_database):
    client = TestClient(app)
    assert client.post(BLUEPRINT, json=INPUT).status_code == 401
    assert client.get("/account/graph-project/not-a-uuid").status_code == 401
    assert client.get(PROJECTS).status_code == 401
