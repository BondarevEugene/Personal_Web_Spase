"""Provision queue contract: auth, idempotency, no billable calls, worker CAS."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from automation.provision_worker import execute_once
from portal.db import engine, session_factory
from server import app

API = "/api/v1/cloud/provision"
SPEC = {
    "name": "test-client-bot", "runtime": "telegram_aiogram",
    "mode": "managed", "provider": "railway", "transport": "webhook",
    "version": "runtime-1.0.0", "max_monthly_usd": 10,
    "secret_refs": ["BOT_TOKEN"],
}


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "provision.sqlite3").as_posix()
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


def register(name):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    result = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": name, "email": name + "@test.example",
        "display_name": "Provision Client", "organization": name + " Org",
        "password": "Strong-Test-Password-2026",
        "password_repeat": "Strong-Test-Password-2026",
    })
    assert result.status_code == 303, result.text
    return c


def csrf(c):
    r = c.get("/api/v1/builder/projects/csrf")
    assert r.status_code == 200
    return {"X-Omni-CSRF": r.json()["csrf_token"]}


def plan(c):
    r = c.post("/api/v1/cloud/plans", headers={
        **csrf(c), "Idempotency-Key": "provision-plan-key-1"},
        json={"spec": SPEC})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def payload(id):
    return {"plan_id": id, "confirmation": "SIMULATE DEPLOYMENT"}


def test_guest_auth_and_capabilities(db_ready):
    guest = TestClient(app)
    assert guest.get(API + "/capabilities").json()["railway_mutations_enabled"] is False
    assert guest.get(API + "/jobs").status_code == 401
    assert guest.post(API + "/jobs", json={
        "plan_id": "00000000-0000-0000-0000-000000000000",
        "confirmation": "SIMULATE DEPLOYMENT",
    }).status_code == 401


def test_job_requires_csrf_exact_confirmation_and_key(db_ready):
    c = register("job_owner")
    id = plan(c)
    assert c.post(API + "/jobs", json=payload(id)).status_code == 403
    assert c.post(API + "/jobs", headers=csrf(c), json=payload(id)).status_code == 422
    assert c.post(API + "/jobs", headers={
        **csrf(c), "Idempotency-Key": "provision-job-key-1"},
        json={"plan_id": id, "confirmation": "DEPLOY LIVE NOW"}).status_code == 422


def test_worker_simulates_exactly_once_and_logs_every_step(db_ready, monkeypatch):
    owner = register("job_single")
    outsider = register("job_other")
    id = plan(owner)
    headers = {**csrf(owner), "Idempotency-Key": "worker-simulation-01"}
    created = owner.post(API + "/jobs", headers=headers, json=payload(id))
    assert created.status_code == 201, created.text
    job = created.json()
    assert job["status"] == "queued"
    assert not job["billable_actions_permitted"]
    assert outsider.get(API + "/jobs/" + job["id"]).status_code == 404
    duplicate = owner.post(API + "/jobs", headers=headers, json=payload(id))
    assert duplicate.json()["id"] == job["id"]
    monkeypatch.setattr("automation.railway_mutations.httpx.Client",
                        lambda **kwargs: (_ for _ in ()).throw(
                            AssertionError("Railway must never be contacted")))
    assert execute_once() == 1
    assert execute_once() == 0
    result = owner.get(API + "/jobs/" + job["id"])
    assert result.status_code == 200
    assert result.json()["status"] == "simulated"
    assert any(event["code"] == "simulation_complete" for event in result.json()["events"])
    assert result.json()["provider_project_id"] is None
    assert result.json()["provider_service_id"] is None
    assert owner.post(API + "/jobs/" + job["id"] + "/cancel",
                      headers=csrf(owner)).status_code == 409


def test_cancel_prevents_worker_execution(db_ready):
    c = register("job_cancel")
    id = plan(c)
    job = c.post(API + "/jobs", headers={
        **csrf(c), "Idempotency-Key": "cancel-job-key-1"},
        json=payload(id)).json()
    response = c.post(API + "/jobs/" + job["id"] + "/cancel", headers=csrf(c))
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert execute_once() == 0


def test_graphql_mutations_are_fixed_and_unavailable_from_public_api():
    from automation.railway_mutations import PROJECT_CREATE, SERVICE_CREATE, RailwayGraphQLAdapter
    assert "projectCreate" in PROJECT_CREATE
    assert "serviceCreate" in SERVICE_CREATE
    with pytest.raises(ValueError):
        RailwayGraphQLAdapter("")
    client = TestClient(app)
    assert "/api/v1/cloud/provision/mutate" not in app.openapi()["paths"]
    assert client.get("/studio-assets/bot_lab.js").status_code == 200
