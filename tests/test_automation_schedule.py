"""Preflight recommendations and explicit schedule worker regression checks."""
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation.diagnostics import analyze
from automation.engine import WorkflowDefinition
from automation.scheduler import tick
from portal.db import engine, session_factory
from portal.models import AutomationSchedule, utcnow
from server import app

client = TestClient(app)
URL = "/api/v1/automation"
FLOW = {"name": "Scheduled demo", "start": "entry",
        "nodes": [
            {"id": "entry", "kind": "trigger", "next": "finish"},
            {"id": "finish", "kind": "end"},
        ]}


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "schedule.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(config, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register():
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    response = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": "scheduleowner", "email": "schedule@example.test",
        "display_name": "Schedule Owner", "organization": "Test Organization",
        "password": "Safe-Test-Password-2026",
        "password_repeat": "Safe-Test-Password-2026",
    })
    assert response.status_code == 303, response.text
    return c


def csrf(c):
    r = c.get("/api/v1/builder/projects/csrf")
    assert r.status_code == 200
    return {"X-Omni-CSRF": r.json()["csrf_token"]}


def test_static_diagnostics_are_explicit_about_limitations():
    workflow = WorkflowDefinition.model_validate({
        "name": "Review me", "start": "trigger",
        "nodes": [
            {"id": "trigger", "kind": "trigger", "next": "publish"},
            {"id": "publish", "kind": "facebook_page", "next": "finish",
             "config": {"page_id": "123", "message": "Hello"}},
            {"id": "finish", "kind": "end"},
            {"id": "unreachable", "kind": "end"},
        ],
    })
    report = analyze(workflow)
    assert report["nodes_total"] == 4
    assert report["nodes_reachable"] == 3
    assert {"credentials", "unreachable", "side_effect"}.issubset({
        w["type"] for w in report["warnings"]})
    assert "не гарантия" in report["limitations"] or "не" in report["limitations"]


def test_interval_schedule_executes_only_one_dry_run_per_due_tick(db_ready):
    c = register()
    created = c.post(URL + "/workflows", headers=csrf(c),
                     json={"definition": FLOW})
    assert created.status_code == 201, created.text
    id = created.json()["id"]
    endpoint = URL + "/workflows/" + id + "/schedule"
    assert c.put(endpoint, json={"interval_minutes": 5}).status_code == 403
    schedule = c.put(endpoint, headers=csrf(c),
                     json={"interval_minutes": 5, "enabled": True})
    assert schedule.status_code == 200, schedule.text
    assert schedule.json()["worker_required"] is True
    with session_factory()() as db:
        item = db.scalar(select(AutomationSchedule).where(
            AutomationSchedule.workflow_id == id))
        item.next_run_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert tick() == 1
    assert tick() == 0
    runs = c.get(URL + "/workflows/" + id + "/runs")
    assert len(runs.json()["runs"]) == 1
    assert runs.json()["runs"][0]["mode"] == "dry_run"
    assert c.delete(URL + "/workflows/" + id, headers=csrf(c)).status_code == 409
    assert c.delete(endpoint, headers=csrf(c)).status_code == 204


def test_static_review_api_is_public_but_side_effect_free():
    response = client.post(URL + "/analyze", json=FLOW)
    assert response.status_code == 200
    assert response.json()["nodes_reachable"] == 2
