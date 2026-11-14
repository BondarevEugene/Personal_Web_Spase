"""Bot security: encrypted token, owner checks, exact-user invitations and audit."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation import bot_vault
from portal.db import engine, session_factory
from portal.models import BotAccessGrant, BotCredential, BotSecurityAudit
from server import app

ROOT = "/api/v1/bot-security"
BOT_TOKEN = "123456789:" + "A" * 35


@pytest.fixture
def database(tmp_path, monkeypatch):
    database_url = "sqlite:///" + (tmp_path / "bot_security.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", database_url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", database_url)
    monkeypatch.setenv("OMNI_BOT_VAULT_FERNET_KEY", Fernet.generate_key().decode())
    engine.cache_clear()
    session_factory.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(config, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(username):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    response = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username,
        "email": username + "@test.example",
        "display_name": "Bot Lab Security",
        "organization": username + " Company",
        "password": "Secure-Test-Password-2026",
        "password_repeat": "Secure-Test-Password-2026",
    })
    assert response.status_code == 303, response.text
    return c


def csrf(c):
    response = c.get("/api/v1/builder/projects/csrf")
    assert response.status_code == 200, response.text
    return {"X-Omni-CSRF": response.json()["csrf_token"]}


def project(c):
    scenario = {
        "name": "Protected Client Bot", "start": "start",
        "nodes": [
            {"id": "start", "kind": "message", "text": "Hello", "next": "end"},
            {"id": "end", "kind": "end", "text": "Bye"},
        ],
    }
    response = c.post("/api/v1/builder/projects", headers=csrf(c),
                      json={"scenario": scenario})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_guest_and_cross_tenant_denied(database):
    guest = TestClient(app)
    owner = register("secure_owner")
    stranger = register("secure_stranger")
    project_id = project(owner)
    path = ROOT + "/bots/" + project_id + "/credential"
    assert guest.get(path).status_code == 401
    assert stranger.get(path).status_code == 404
    assert stranger.put(path, headers=csrf(stranger),
                        json={"token": BOT_TOKEN}).status_code == 404
    assert stranger.get(ROOT + "/bots/" + project_id + "/access").status_code == 404
    assert stranger.get(ROOT + "/bots/" + project_id + "/audit").status_code == 404
    assert owner.put(path, json={"token": BOT_TOKEN}).status_code == 403
    assert owner.put(path, headers=csrf(owner),
                     json={"token": "wrong"}).status_code == 422


def test_vault_encrypts_never_leaks_and_can_rotate(database, monkeypatch):
    owner = register("vault_owner")
    project_id = project(owner)
    path = ROOT + "/bots/" + project_id + "/credential"
    created = owner.put(path, headers=csrf(owner), json={"token": BOT_TOKEN})
    assert created.status_code == 200, created.text
    assert created.json()["configured"] is True
    assert created.json()["verified"] is False
    assert BOT_TOKEN not in created.text
    assert BOT_TOKEN not in owner.get(path).text
    with session_factory()() as db:
        row = db.scalar(select(BotCredential))
        assert BOT_TOKEN not in row.ciphertext
        assert BOT_TOKEN not in row.fingerprint
        assert bot_vault.decrypt_token(row.owner_id, row.project_id, row.ciphertext) == BOT_TOKEN
        with pytest.raises(bot_vault.BotVaultUnavailable):
            bot_vault.decrypt_token(row.owner_id, "11111111-1111-1111-1111-111111111111",
                                    row.ciphertext)
    monkeypatch.setattr(bot_vault, "telegram_get_me",
                        lambda token: {"bot_id": "12345", "username": "Client_Bot"}
                        if token == BOT_TOKEN else None)
    verified = owner.post(path + "/verify", headers=csrf(owner))
    assert verified.status_code == 200, verified.text
    assert verified.json()["username"] == "Client_Bot"
    assert BOT_TOKEN not in verified.text
    new_token = "123456789:" + "B" * 35
    rotation = owner.put(path, headers=csrf(owner), json={"token": new_token})
    assert rotation.status_code == 200
    assert rotation.json()["verified"] is False
    with session_factory()() as db:
        row = db.scalar(select(BotCredential))
        assert bot_vault.decrypt_token(row.owner_id, row.project_id, row.ciphertext) == new_token
    deleted = owner.delete(path, headers=csrf(owner))
    assert deleted.status_code == 204
    assert owner.get(path).json()["configured"] is False
    with session_factory()() as db:
        events = db.scalars(select(BotSecurityAudit)).all()
        assert {"credential_added", "telegram_verified", "credential_rotated",
                "credential_deleted"}.issubset({event.event for event in events})


def test_target_bound_single_use_invitation_and_revoke(database):
    owner = register("invite_owner")
    target = register("invite_target")
    intruder = register("invite_other")
    project_id = project(owner)
    invite_url = ROOT + "/bots/" + project_id + "/invitations"
    created = owner.post(invite_url, headers=csrf(owner),
                         json={"username": "invite_target", "role": "viewer"})
    assert created.status_code == 201, created.text
    token = created.json()["one_time_token"]
    assert len(token) > 32
    assert token not in str(owner.get(invite_url).json())
    accept = ROOT + "/invitations/accept"
    assert intruder.post(accept, headers=csrf(intruder),
                         json={"token": token}).status_code == 404
    assert target.post(accept, json={"token": token}).status_code == 403
    accepted = target.post(accept, headers=csrf(target), json={"token": token})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["role"] == "viewer"
    assert target.post(accept, headers=csrf(target),
                       json={"token": token}).status_code == 404
    assert len(target.get(ROOT + "/shared").json()["bots"]) == 1
    assert len(intruder.get(ROOT + "/shared").json()["bots"]) == 0
    assert target.get(ROOT + "/bots/" + project_id + "/credential").status_code == 404
    assert target.get("/api/v1/builder/projects/" + project_id).status_code == 404
    assert target.get("/api/v1/cloud/plans").json()["plans"] == []
    members = owner.get(ROOT + "/bots/" + project_id + "/access").json()["members"]
    assert len(members) == 1 and members[0]["role"] == "viewer"
    assert owner.delete(ROOT + "/bots/" + project_id + "/access/" + members[0]["id"],
                        headers=csrf(owner)).status_code == 204
    assert target.get(ROOT + "/shared").json()["bots"] == []


def test_cancel_invite_and_role_bound(database):
    owner = register("revoke_owner")
    target = register("revoke_target")
    bot_id = project(owner)
    base = ROOT + "/bots/" + bot_id + "/invitations"
    create = owner.post(base, headers=csrf(owner),
                        json={"username": "revoke_target", "role": "operator"})
    assert create.status_code == 201
    invitation = create.json()
    assert invitation["role"] == "operator"
    listed = owner.get(base).json()["invitations"]
    assert len(listed) == 1
    assert "one_time_token" not in str(listed)
    assert owner.delete(base + "/" + invitation["id"],
                        headers=csrf(owner)).status_code == 204
    rejected = target.post(ROOT + "/invitations/accept", headers=csrf(target),
                           json={"token": invitation["one_time_token"]})
    assert rejected.status_code == 404
    assert owner.post(base, headers=csrf(owner), json={
        "username": "revoke_target", "role": "owner"}).status_code == 422


def test_no_vault_key_means_fail_closed(database, monkeypatch):
    c = register("missing_key")
    bot_id = project(c)
    monkeypatch.delenv("OMNI_BOT_VAULT_FERNET_KEY")
    response = c.put(ROOT + "/bots/" + bot_id + "/credential", headers=csrf(c),
                     json={"token": BOT_TOKEN})
    assert response.status_code == 503
    assert c.get(ROOT + "/capabilities").json()["vault_configured"] is False
    with session_factory()() as db:
        assert db.scalar(select(BotCredential)) is None


def test_no_telegram_secrets_in_ui_or_shared_results(database):
    c = register("display_owner")
    bot_id = project(c)
    result = c.get("/bots/lab")
    assert result.status_code == 200
    assert "lab-security-workbench" in result.text
    assert "lab-invite-create" in result.text
    assert "lab-accept-token" in result.text
    script = c.get("/studio-assets/bot_lab.js")
    assert script.status_code == 200
    assert "localStorage" not in script.text
    assert "storeBotToken" in script.text
    assert "acceptInvitation" in script.text
