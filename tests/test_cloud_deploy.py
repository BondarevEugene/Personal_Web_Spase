"""Cloud Deploy foundation: validation, ownership, idempotency and no side effects."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError

from automation.deployment import DeploymentSpec, RailwayProvider, build_plan
from portal.db import engine, session_factory
from server import app

URL = "/api/v1/cloud"
SPEC = {
    "name": "client-bot",
    "runtime": "telegram_aiogram",
    "mode": "managed",
    "provider": "railway",
    "transport": "webhook",
    "version": "runtime-1.0.0",
    "max_monthly_usd": 10,
    "secret_refs": ["BOT_TOKEN", "WEBHOOK_SECRET"],
}


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "cloud.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    conf = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(conf, "head")
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
        "display_name": "Cloud Client", "organization": username + " Org",
        "password": "Strong-Cloud-Password-2026",
        "password_repeat": "Strong-Cloud-Password-2026",
    })
    assert response.status_code == 303, response.text
    return c


def csrf(c):
    res = c.get("/api/v1/builder/projects/csrf")
    assert res.status_code == 200, res.text
    return {"X-Omni-CSRF": res.json()["csrf_token"]}


def test_immutable_plan_and_no_live_provider():
    plan = build_plan(DeploymentSpec.model_validate(SPEC))
    same = build_plan(DeploymentSpec.model_validate(dict(SPEC)))
    assert plan.manifest_sha256 == same.manifest_sha256
    assert not plan.creates_resources
    assert plan.estimated_usd is None
    assert plan.state == "planned"
    assert RailwayProvider().readiness()["deploy"] == "disabled"
    with pytest.raises(NotImplementedError):
        RailwayProvider().provision()


def test_rejects_secrets_and_unsupported_modes():
    for overrides in [
        {"secret_refs": ["RAILWAY_PASSWORD"]},
        {"secret_refs": ["BOT_TOKEN", "BOT_TOKEN"]},
        {"mode": "managed", "provider": "cloud_run"},
        {"max_monthly_usd": 0},
        {"version": "latest"},
        {"name": "Invalid Name"},
    ]:
        with pytest.raises(ValidationError):
            DeploymentSpec.model_validate({**SPEC, **overrides})


def test_cloud_capabilities_and_preview_never_create_resources():
    c = TestClient(app)
    capabilities = c.get(URL + "/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["live_deployment_enabled"] is False
    preview = c.post(URL + "/preview", json={"spec": SPEC})
    assert preview.status_code == 200, preview.text
    assert preview.json()["state"] == "planned"
    assert preview.json()["creates_resources"] is False
    assert preview.json()["estimated_usd"] is None
    assert c.get(URL + "/plans").status_code == 401


def test_tenant_isolation_and_csrf(db_ready):
    one = register("cloud_one")
    two = register("cloud_two")
    assert one.post(URL + "/plans", json={"spec": SPEC}).status_code == 403
    assert one.post(URL + "/plans", headers=csrf(one), json={"spec": SPEC}).status_code == 422
    headers = {**csrf(one), "Idempotency-Key": "deploy-one-v1"}
    created = one.post(URL + "/plans", headers=headers, json={"spec": SPEC})
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["status"] == "planned"
    assert item["provider"] == "railway"
    assert one.get(URL + "/plans/" + item["id"]).status_code == 200
    assert two.get(URL + "/plans/" + item["id"]).status_code == 404
    assert two.get(URL + "/plans").json() == {"plans": []}
    again = one.post(URL + "/plans", headers=headers, json={"spec": SPEC})
    assert again.status_code == 201
    assert again.json()["id"] == item["id"]
    conflict = one.post(URL + "/plans", headers=headers, json={
        "spec": {**SPEC, "max_monthly_usd": 25},
    })
    assert conflict.status_code == 409
    assert len(one.get(URL + "/plans").json()["plans"]) == 1


def test_managed_cloud_page_is_accessible_from_home_and_has_real_controls():
    c = TestClient(app)
    page = c.get("/cloud/deploy")
    assert page.status_code == 200, page.text
    assert 'id="cloud-preview"' in page.text
    assert 'id="cloud-save"' in page.text
    assert "создание платных ресурсов Railway пока отключено".lower() in page.text.lower()
    assert c.get("/studio-assets/cloud_deploy.js").status_code == 200
    assert 'href="/cloud/deploy"' in c.get("/").text
    paths = app.openapi()["paths"]
    for path in ("/api/v1/cloud/capabilities", "/api/v1/cloud/preview",
                 "/api/v1/cloud/plans", "/api/v1/cloud/plans/{deployment_id}"):
        assert path in paths
