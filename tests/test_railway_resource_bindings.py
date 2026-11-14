"""Railway resource binding: live read-only verification and customer isolation."""
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation import railway_oauth
from automation.railway_inspection import RailwayInspectError, inspect_binding
from portal.db import engine, session_factory
from portal.models import CloudOAuthConnection, Customer, utcnow
from server import app

ROOT = "/api/v1/cloud/resources"
SPEC = {
    "name": "railway-client", "mode": "byoc", "provider": "railway",
    "runtime": "telegram_aiogram", "transport": "webhook",
    "version": "runtime-1.0.0", "max_monthly_usd": 12,
    "secret_refs": ["BOT_TOKEN"],
}
PROJECT = "project-resource-12345"
SERVICE = "service-resource-12345"
ENVIRONMENT = "environment-prod-12345"


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "resource_binding.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.setenv("OMNI_CLOUD_OAUTH_FERNET_KEY", Fernet.generate_key().decode())
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
    response = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username, "email": username + "@test.example",
        "display_name": "Railway User", "organization": username + " org",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert response.status_code == 303, response.text
    return c


def csrf(c):
    response = c.get("/api/v1/builder/projects/csrf")
    assert response.status_code == 200
    return {"X-Omni-CSRF": response.json()["csrf_token"]}


def create_plan(c, key):
    response = c.post("/api/v1/cloud/plans", headers={
        **csrf(c), "Idempotency-Key": key},
        json={"spec": SPEC})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def connect(username):
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(Customer.username == username))
        row = CloudOAuthConnection(
            customer_id=customer.id, provider="railway",
            remote_subject="remote-" + username,
            remote_name="Railway Team",
            scopes="openid project:member",
            access_ciphertext=railway_oauth.encrypt("auth-test-token-" + username),
            refresh_ciphertext=None,
            expires_at=utcnow() + timedelta(hours=1),
            created_at=utcnow(), updated_at=utcnow())
        db.add(row)
        db.commit()


def sample_provider(token, project_id, service_id, environment_id):
    assert token.startswith("auth-test-token-")
    assert (project_id, service_id, environment_id) == (PROJECT, SERVICE, ENVIRONMENT)
    return {
        "project": {"id": PROJECT, "name": "Customer project"},
        "service": {"id": SERVICE, "name": "Bot worker"},
        "environment": {"id": ENVIRONMENT},
        "instance": {"id": "instance-1", "region": "eu", "replicas": 1,
                     "healthcheck_configured": True},
        "deployment": {"id": "deployment-123", "status": "SUCCESS",
                       "created_at": "2026-11-14T10:00:00Z"},
        "source": "railway_graphql", "bot_health_verified": False}


def test_auth_and_csrf(db_ready):
    guest = TestClient(app)
    valid = {"plan_id": "00000000-0000-0000-0000-000000000000",
             "project_id": PROJECT, "service_id": SERVICE,
             "environment_id": ENVIRONMENT}
    assert guest.post(ROOT + "/bindings", json=valid).status_code == 401
    user = register("bind_owner")
    plan_id = create_plan(user, "bind-owner-plan-key")
    assert user.post(ROOT + "/bindings",
                     json={**valid, "plan_id": plan_id}).status_code == 403
    assert user.post(ROOT + "/bindings", json={**valid, "plan_id": plan_id},
                     headers=csrf(user)).status_code == 409


def test_owner_verifies_real_resources_and_reads_provider_status(db_ready, monkeypatch):
    owner = register("bind_real")
    stranger = register("bind_other")
    plan_id = create_plan(owner, "bind-real-plan-key")
    connect("bind_real")
    monkeypatch.setattr("api.railway_resources.inspect_binding", sample_provider)
    body = {"plan_id": plan_id, "project_id": PROJECT,
            "service_id": SERVICE, "environment_id": ENVIRONMENT}
    created = owner.post(ROOT + "/bindings", headers=csrf(owner), json=body)
    assert created.status_code == 200, created.text
    binding = created.json()["binding"]
    assert binding["last_provider_status"] == "SUCCESS"
    assert created.json()["provider"]["bot_health_verified"] is False
    assert created.json()["note"] == "Existing Railway service linked; no resources were created"
    duplicate = owner.post(ROOT + "/bindings", headers=csrf(owner), json=body)
    assert duplicate.status_code == 200
    assert duplicate.json()["binding"]["id"] == binding["id"]
    assert stranger.get(ROOT + "/bindings/" + plan_id).status_code == 404
    assert stranger.get(ROOT + "/bindings/" + plan_id + "/inspect").status_code == 404
    assert owner.get(ROOT + "/bindings/" + plan_id).json()["binding"]["service_id"] == SERVICE
    checked = owner.get(ROOT + "/bindings/" + plan_id + "/inspect")
    assert checked.status_code == 200, checked.text
    assert checked.json()["deployment_is_bot_healthy"] is False
    assert checked.json()["provider"]["deployment"]["id"] == "deployment-123"
    readiness = owner.get("/api/v1/bot-lab/deploy-readiness/" + plan_id)
    assert readiness.status_code == 200
    checks = {entry["code"]: entry["ok"] for entry in readiness.json()["checks"]}
    assert checks["verified_service"] is True
    assert checks["application_health"] is False
    assert readiness.json()["ready"] is False
    assert owner.delete(ROOT + "/bindings/" + plan_id).status_code == 403
    assert owner.delete(ROOT + "/bindings/" + plan_id, headers=csrf(owner)).status_code == 204
    assert owner.get(ROOT + "/bindings/" + plan_id).json()["binding"] is None


def test_provider_refuses_foreign_or_invalid_resource_ids(db_ready, monkeypatch):
    owner = register("bind_denied")
    plan_id = create_plan(owner, "bind-denied-plan-key")
    connect("bind_denied")
    def refuse(*args):
        raise RailwayInspectError("Selected service/environment does not belong to this project")
    monkeypatch.setattr("api.railway_resources.inspect_binding", refuse)
    response = owner.post(ROOT + "/bindings", headers=csrf(owner), json={
        "plan_id": plan_id, "project_id": PROJECT,
        "service_id": SERVICE, "environment_id": ENVIRONMENT})
    assert response.status_code == 422
    assert owner.get(ROOT + "/bindings/" + plan_id).json()["binding"] is None


def test_railway_graphql_inspection_checks_project_membership(monkeypatch):
    calls = []
    def fake_query(token, query, variables):
        calls.append(variables)
        if "project" in variables:
            return {"project": {
                "id": PROJECT, "name": "Selected",
                "services": {"edges": [{"node": {"id": SERVICE}}]},
                "environments": {"edges": [{"node": {"id": ENVIRONMENT}}]},
            }}
        return {"serviceInstance": {
            "id": "instance-123", "serviceName": "Worker",
            "region": "eu", "numReplicas": 1, "healthcheckPath": "/health",
            "latestDeployment": {"id": "dep-1", "status": "SUCCESS",
                                 "createdAt": "2026-11-14T10:00:00Z"},
        }}
    monkeypatch.setattr("automation.railway_inspection._query", fake_query)
    result = inspect_binding("test-token", PROJECT, SERVICE, ENVIRONMENT)
    assert result["deployment"]["status"] == "SUCCESS"
    assert not result["bot_health_verified"]
    assert len(calls) == 2
    with pytest.raises(RailwayInspectError):
        inspect_binding("test-token", PROJECT, "foreign-service-id", ENVIRONMENT)
    with pytest.raises(RailwayInspectError):
        inspect_binding("test-token", PROJECT, SERVICE, "127.0.0.1")


def test_studio_resources_are_displayed_and_routes_registered():
    page = TestClient(app).get("/studio-assets/bot_lab.js")
    assert page.status_code == 200
    for token in ("loadResourceOptions", "bindResource", "inspectResource",
                  "unlinkResource", "lab-resource-report"):
        assert token in page.text
    paths = app.openapi()["paths"]
    for path in (ROOT + "/bindings",
                 ROOT + "/bindings/{plan_id}",
                 ROOT + "/bindings/{plan_id}/inspect"):
        assert path in paths
