"""Secure release gate: ownership, OCI pin, immutable snapshot, replay and invalidation."""
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation import bot_vault
from automation.release_gate import allowed_image
from portal.db import engine, session_factory
from portal.models import (BotCredential, BuilderProject, CloudOAuthConnection,
                           CloudRailwayBinding, CloudReleaseReview, Customer, utcnow)
from server import app

API = "/api/v1/cloud/releases"
IMAGE = "registry.example.com/omni/telegram@sha256:" + "a" * 64
TOKEN = "123456789:" + "B" * 35
SPEC = {
    "name": "release-client", "runtime": "telegram_aiogram",
    "mode": "byoc", "provider": "railway", "transport": "webhook",
    "version": "runtime-1.0.0", "max_monthly_usd": 10,
    "secret_refs": ["BOT_TOKEN"],
}


@pytest.fixture
def database(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "release.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.setenv("OMNI_BOT_VAULT_FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM", IMAGE)
    engine.cache_clear()
    session_factory.cache_clear()
    conf = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(conf, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def user(username):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    r = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username, "email": username + "@test.example",
        "display_name": "Secure Release", "organization": username + " Org",
        "password": "Strong-Release-Test-2026",
        "password_repeat": "Strong-Release-Test-2026",
    })
    assert r.status_code == 303, r.text
    return c


def csrf(c):
    r = c.get("/api/v1/builder/projects/csrf")
    assert r.status_code == 200, r.text
    return {"X-Omni-CSRF": r.json()["csrf_token"]}


def create_bot(c):
    r = c.post("/api/v1/builder/projects", headers=csrf(c), json={
        "scenario": {"name": "Secure Telegram", "start": "start",
                     "nodes": [{"id": "start", "kind": "message",
                                "text": "Hi", "next": "end"},
                               {"id": "end", "kind": "end", "text": "Bye"}]}})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def create_plan(c):
    r = c.post("/api/v1/cloud/plans", headers={**csrf(c),
        "Idempotency-Key": "secure-release-plan-01"}, json={"spec": SPEC})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def make_ready(c, bot_id, plan_id, monkeypatch):
    monkeypatch.setattr(bot_vault, "telegram_get_me",
                        lambda token: {"bot_id": "111222", "username": "Secure_Bot"})
    r = c.put("/api/v1/bot-security/bots/" + bot_id + "/credential",
              headers=csrf(c), json={"token": TOKEN})
    assert r.status_code == 200, r.text
    v = c.post("/api/v1/bot-security/bots/" + bot_id + "/credential/verify",
               headers=csrf(c))
    assert v.status_code == 200, v.text
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(Customer.username == "release_owner"))
        db.add(CloudOAuthConnection(
            customer_id=customer.id, provider="railway", remote_subject="railway-owner",
            remote_name="Railway", scopes="project:member",
            access_ciphertext="encrypted-placeholder", refresh_ciphertext=None,
            expires_at=utcnow()+timedelta(hours=1), created_at=utcnow(), updated_at=utcnow()))
        db.add(CloudRailwayBinding(
            customer_id=customer.id, deployment_id=plan_id,
            project_id="project-id-1", environment_id="env-id-1", service_id="svc-id-1",
            verified_at=utcnow(), created_at=utcnow(), updated_at=utcnow()))
        db.commit()


def review(c, bot, plan, key="release-request-01"):
    return c.post(API + "/reviews", headers={
        **csrf(c), "Idempotency-Key": key},
        json={"bot_project_id": bot, "cloud_plan_id": plan,
              "confirmation": "REQUEST RELEASE REVIEW"})


def test_operator_image_must_be_pinned(monkeypatch):
    monkeypatch.setenv("OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM",
                       "registry.example.com/omni/telegram:latest")
    assert allowed_image("telegram_aiogram") is None
    monkeypatch.setenv("OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM", IMAGE)
    assert allowed_image("telegram_aiogram") == IMAGE


def test_owner_preflight_and_no_external_mutations(database, monkeypatch):
    owner = user("release_owner")
    stranger = user("release_other")
    bot = create_bot(owner)
    plan = create_plan(owner)
    guest = TestClient(app)
    assert guest.get(API+"/preflight/"+bot+"/"+plan).status_code == 401
    assert stranger.get(API+"/preflight/"+bot+"/"+plan).status_code == 404
    initial = owner.get(API+"/preflight/"+bot+"/"+plan).json()
    assert initial["ready_for_review"] is False
    assert initial["ready_for_paid_deployment"] is False
    assert initial["creates_resources"] is False
    assert initial["estimated_cost_usd"] is None
    assert review(owner, bot, plan).status_code == 409
    make_ready(owner, bot, plan, monkeypatch)
    checks = owner.get(API+"/preflight/"+bot+"/"+plan).json()
    assert checks["ready_for_review"] is True
    assert checks["ready_for_paid_deployment"] is False
    assert any(x["code"]=="price_quote" and not x["ok"] for x in checks["checks"])
    assert owner.post(API+"/reviews",json={"bot_project_id":bot,
        "cloud_plan_id":plan,"confirmation":"REQUEST RELEASE REVIEW"}).status_code == 403
    r = review(owner,bot,plan)
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    assert r.json()["billable_actions_permitted"] is False
    assert stranger.get(API+"/reviews/"+rid).status_code == 404
    assert r.json()["id"] == review(owner,bot,plan).json()["id"]
    assert owner.get(API+"/reviews/"+rid).json()["still_valid"] is True
    assert len(owner.get(API+"/reviews").json()["reviews"]) == 1
    # Owner rotates Telegram token; the previously approved identity is invalid.
    rotated = owner.put("/api/v1/bot-security/bots/"+bot+"/credential",
                        headers=csrf(owner),json={"token":"123456789:"+"C"*35})
    assert rotated.status_code == 200
    assert owner.get(API+"/reviews/"+rid).json()["still_valid"] is False
    assert owner.post(API+"/reviews/"+rid+"/cancel",headers=csrf(owner)).status_code == 200
    assert owner.get(API+"/reviews/"+rid).json()["status"] == "cancelled"
    with session_factory()() as db:
        assert db.scalar(select(CloudReleaseReview)).cancelled_at is not None


def test_bad_confirmation_and_unknown_plan(database):
    owner = user("review_error")
    bot = create_bot(owner)
    plan = create_plan(owner)
    assert owner.get(API+"/preflight/"+bot+"/00000000-0000-0000-0000-000000000000").status_code == 404
    response = owner.post(API+"/reviews",headers={**csrf(owner),
        "Idempotency-Key":"bad-confirmation-01"},json={"bot_project_id":bot,
        "cloud_plan_id":plan,"confirmation":"DEPLOY AND CHARGE"})
    assert response.status_code == 422
    assert TestClient(app).get(API+"/capabilities").json()["live_railway_mutations_enabled"] is False


def test_editing_bot_scenario_invalidates_immutable_release(database, monkeypatch):
    owner = user("release_owner")
    bot = create_bot(owner)
    plan = create_plan(owner)
    make_ready(owner, bot, plan, monkeypatch)
    created = review(owner, bot, plan, key="scenario-review-key-01")
    assert created.status_code == 201, created.text
    rid = created.json()["id"]
    assert owner.get(API + "/reviews/" + rid).json()["still_valid"] is True
    changed = {
        "scenario": {
            "name": "Secure Telegram", "start": "start",
            "nodes": [
                {"id": "start", "kind": "message", "text": "New content", "next": "end"},
                {"id": "end", "kind": "end", "text": "Bye"},
            ],
        }
    }
    update = owner.put("/api/v1/builder/projects/" + bot, headers=csrf(owner),
                       json=changed)
    assert update.status_code == 200, update.text
    assert owner.get(API + "/reviews/" + rid).json()["still_valid"] is False
    assert owner.post(API + "/reviews", headers={
        **csrf(owner), "Idempotency-Key": "scenario-review-key-01"},
        json={"bot_project_id": bot, "cloud_plan_id": plan,
              "confirmation": "REQUEST RELEASE REVIEW"}).status_code == 409
