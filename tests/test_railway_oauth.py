"""Railway OAuth tests: encrypted persistence, PKCE, state isolation, replay and rotation."""
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation import railway_oauth as oauth
from portal.db import engine, session_factory
from portal.models import CloudOAuthAttempt, CloudOAuthConnection
from server import app

BASE = "/api/v1/cloud/railway"


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "railway_oauth.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.setenv("OMNI_RAILWAY_OAUTH_CLIENT_ID", "railway-test-client")
    monkeypatch.setenv("OMNI_RAILWAY_OAUTH_CLIENT_SECRET", "railway-test-secret")
    monkeypatch.setenv("OMNI_RAILWAY_OAUTH_REDIRECT_URI",
                       "http://127.0.0.1:8001/api/v1/cloud/railway/callback")
    monkeypatch.setenv("OMNI_CLOUD_OAUTH_FERNET_KEY", Fernet.generate_key().decode())
    engine.cache_clear()
    session_factory.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(config, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(name):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    r = c.post("/account/register", follow_redirects=False, data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": name, "email": name + "@test.example",
        "display_name": "Railway Tester", "organization": name + " Ltd",
        "password": "Strong-Test-Password-2026",
        "password_repeat": "Strong-Test-Password-2026",
    })
    assert r.status_code == 303, r.text
    return c


def csrf(c):
    r = c.get("/api/v1/builder/projects/csrf")
    assert r.status_code == 200, r.text
    return {"X-Omni-CSRF": r.json()["csrf_token"]}


def authorize(c):
    response = c.post(BASE + "/authorize", headers=csrf(c))
    assert response.status_code == 200, response.text
    url = urlparse(response.json()["authorization_url"])
    assert url.scheme == "https" and url.hostname == "backboard.railway.com"
    args = parse_qs(url.query)
    assert args["code_challenge_method"] == ["S256"]
    assert args["prompt"] == ["consent"]
    assert "offline_access" in args["scope"][0]
    assert args["code_challenge"][0]
    return args["state"][0]


def test_pkce_and_cipher_never_use_plaintext(db_ready):
    assert oauth.readiness()["configured"] is True
    state, verifier, challenge = oauth.new_attempt()
    assert len(state) > 30 and len(challenge) >= 43
    assert state != challenge and verifier != challenge
    encrypted = oauth.encrypt("provider-refresh-secret")
    assert "provider-refresh-secret" not in encrypted
    assert oauth.decrypt(encrypted) == "provider-refresh-secret"
    with pytest.raises(oauth.OAuthConfigurationError):
        oauth.decrypt("wrong-key-or-malformed")


def test_unauthorized_access_and_csrf_rejected(db_ready):
    c = TestClient(app)
    assert c.get(BASE + "/status").status_code == 401
    assert c.post(BASE + "/authorize").status_code == 401
    owner = register("oauth_owner")
    assert owner.post(BASE + "/authorize").status_code == 403
    assert owner.delete(BASE + "/disconnect").status_code == 403


def test_authorization_roundtrip_replay_and_refresh_rotation(db_ready, monkeypatch):
    c = register("oauth_connected")
    state = authorize(c)
    with session_factory()() as db:
        row = db.scalar(select(CloudOAuthAttempt))
        assert row and row.state_hash == oauth.state_hash(state)
        assert state not in row.verifier_ciphertext
        assert oauth.decrypt(row.verifier_ciphertext)
    observed = {}
    def fake_exchange(code, verifier):
        assert code == "code-from-railway"
        observed["verifier"] = verifier
        return {"access_token": "access-A", "refresh_token": "refresh-A",
                "expires_in": 3600, "scope": oauth.SCOPES}
    monkeypatch.setattr(oauth, "exchange_code", fake_exchange)
    monkeypatch.setattr(oauth, "profile", lambda token: {
        "sub": "railway-user-123", "name": "Railway Client"})
    callback = c.get(BASE + "/callback", params={
        "code": "code-from-railway", "state": state, "iss": oauth.ISSUER},
        follow_redirects=False)
    assert callback.status_code == 303
    assert callback.headers["location"] == "/cloud/deploy?railway=connected"
    assert observed["verifier"]
    details = c.get(BASE + "/status").json()
    assert details["connected"] is True
    assert details["subject"] == "railway-user-123"
    assert "access-A" not in str(details) and "refresh-A" not in str(details)
    with session_factory()() as db:
        row = db.scalar(select(CloudOAuthConnection))
        assert row.access_ciphertext != "access-A"
        assert row.refresh_ciphertext != "refresh-A"
        assert oauth.decrypt(row.refresh_ciphertext) == "refresh-A"
    replay = c.get(BASE + "/callback",
                   params={"state": state, "code": "code-from-railway"},
                   follow_redirects=False)
    assert replay.status_code == 400
    def fake_refresh(value):
        assert value == "refresh-A"
        return {"access_token": "access-B", "refresh_token": "refresh-B",
                "expires_in": 3600, "scope": oauth.SCOPES}
    monkeypatch.setattr(oauth, "refresh_token", fake_refresh)
    updated = c.post(BASE + "/refresh", headers=csrf(c))
    assert updated.status_code == 200
    assert "access-B" not in str(updated.json())
    with session_factory()() as db:
        row = db.scalar(select(CloudOAuthConnection))
        assert oauth.decrypt(row.refresh_ciphertext) == "refresh-B"
    assert c.delete(BASE + "/disconnect", headers=csrf(c)).status_code == 204
    assert c.get(BASE + "/status").json()["connected"] is False


def test_cross_customer_state_and_no_token_exposure(db_ready, monkeypatch):
    one = register("oauth_first")
    two = register("oauth_second")
    state = authorize(one)
    called = []
    monkeypatch.setattr(oauth, "exchange_code", lambda *args: called.append(True))
    bad = two.get(BASE + "/callback", params={"code": "bad", "state": state})
    assert bad.status_code == 400
    assert not called
    assert two.get(BASE + "/status").json()["connected"] is False
    assert one.get(BASE + "/status").json()["connected"] is False


def test_bad_provider_exchange_consumes_state(db_ready, monkeypatch):
    c = register("oauth_broken")
    state = authorize(c)
    monkeypatch.setattr(oauth, "exchange_code",
                        lambda *args: (_ for _ in ()).throw(oauth.OAuthProviderError()))
    bad = c.get(BASE + "/callback", params={"code": "fail", "state": state},
                follow_redirects=False)
    assert bad.status_code == 303
    assert bad.headers["location"].endswith("railway=failed")
    again = c.get(BASE + "/callback", params={"code": "fail", "state": state})
    assert again.status_code == 400


def test_ui_has_connection_controls(db_ready):
    r = TestClient(app).get("/cloud/deploy")
    assert r.status_code == 200
    for control in ("railway-connect", "railway-refresh", "railway-disconnect",
                    "railway-connection-status"):
        assert 'id="' + control + '"' in r.text
    assert TestClient(app).get("/studio-assets/cloud_deploy.js").status_code == 200
