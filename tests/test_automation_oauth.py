"""OAuth route integration tests: encrypted tokens, replay, tenant and disconnect."""
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api import automation_connections, automation_oauth
from portal.db import Base
from portal.models import AutomationConnection, AutomationCredential

USER_ID = "00000000-0000-0000-0000-000000000001"


def test_oauth_flow_encrypted_and_one_time(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    user = SimpleNamespace(id=USER_ID, role="owner")
    monkeypatch.setattr(automation_oauth, "session_factory", lambda: lambda: Session(engine))
    monkeypatch.setattr(automation_connections, "session_factory", lambda: lambda: Session(engine))
    monkeypatch.setattr(automation_connections, "require_user", lambda req, db: user)
    monkeypatch.setattr(automation_connections, "csrf", lambda req: None)
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", Fernet.generate_key().decode())
    monkeypatch.setenv("OMNI_GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("OMNI_GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("OMNI_OAUTH_REDIRECT_URI",
                       "https://example.org/api/v1/automation/oauth/callback")
    monkeypatch.setattr(automation_oauth, "exchange_code",
                        lambda provider, code, verifier: {"access_token": "private-token"})
    app = FastAPI()
    app.include_router(automation_connections.router)
    app.include_router(automation_oauth.router)
    client = TestClient(app)
    created = client.post("/api/v1/automation/connections",
                          json={"provider": "google_sheets", "label": "Marketing"}).json()
    connection_id = created["id"]
    start = client.post(f"/api/v1/automation/oauth/{connection_id}/start")
    assert start.status_code == 200, start.text
    url = start.json()["authorization_url"]
    query = parse_qs(urlparse(url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert "test-secret" not in url
    state = query["state"][0]
    callback = client.get("/api/v1/automation/oauth/callback",
                          params={"state": state, "code": "example-code"})
    assert callback.status_code == 200, callback.text
    assert callback.json()["status"] == "authorized_unverified"
    assert client.get("/api/v1/automation/oauth/callback",
                      params={"state": state, "code": "example-code"}).status_code == 403
    with Session(engine) as db:
        credential = db.query(AutomationCredential).one()
        assert b"private-token" not in credential.ciphertext
        assert db.query(AutomationConnection).one().status == "authorized_unverified"
    assert client.post(
        f"/api/v1/automation/connections/{connection_id}/disconnect").status_code == 200
    with Session(engine) as db:
        assert db.query(AutomationCredential).count() == 0
    assert client.post(f"/api/v1/automation/oauth/{connection_id}/start").status_code == 409
