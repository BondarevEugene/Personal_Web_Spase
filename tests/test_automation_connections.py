"""Connection Manager API: owner boundary, audit, tenant isolation and no tokens."""
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api import automation_connections as connections
from portal.db import Base
from portal.models import AutomationConnection, AutomationConnectionEvent


def test_registry_is_tenant_scoped_and_append_only(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    user = SimpleNamespace(id="00000000-0000-0000-0000-000000000001", role="owner")
    monkeypatch.setattr(connections, "session_factory", lambda: lambda: Session(engine))
    monkeypatch.setattr(connections, "require_user", lambda request, db: user)
    monkeypatch.setattr(connections, "csrf", lambda request: None)
    app = FastAPI()
    app.include_router(connections.router)
    client = TestClient(app)

    created = client.post("/api/v1/automation/connections", json={
        "provider": "google_sheets", "label": "Main spreadsheet",
    })
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["status"] == "pending_setup"
    assert payload["authorization"] == "not_implemented"
    assert client.get("/api/v1/automation/connections").json()["connections"][0]["id"] == payload["id"]
    assert client.post("/api/v1/automation/connections", json={
        "provider": "google_sheets", "label": "Main spreadsheet",
    }).status_code == 409
    assert client.post("/api/v1/automation/connections", json={
        "provider": "invalid", "label": "Main spreadsheet",
    }).status_code == 422

    disconnected = client.post(
        f"/api/v1/automation/connections/{payload['id']}/disconnect")
    assert disconnected.status_code == 200
    assert disconnected.json()["status"] == "disconnected"
    assert len(client.get(
        f"/api/v1/automation/connections/{payload['id']}/audit").json()["events"]) == 2
    with Session(engine) as db:
        assert db.query(AutomationConnection).count() == 1
        assert db.query(AutomationConnectionEvent).count() == 2
    user.id = "00000000-0000-0000-0000-000000000002"
    assert client.get(
        f"/api/v1/automation/connections/{payload['id']}").status_code == 404
    assert client.get("/api/v1/automation/connections").json()["connections"] == []


def test_connection_mutations_require_owner_and_csrf(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    user = SimpleNamespace(id="00000000-0000-0000-0000-000000000003", role="member")
    monkeypatch.setattr(connections, "session_factory", lambda: lambda: Session(engine))
    monkeypatch.setattr(connections, "require_user", lambda request, db: user)
    monkeypatch.setattr(connections, "csrf", lambda request: (_ for _ in ()).throw(
        HTTPException(403, "CSRF required")))
    app = FastAPI()
    app.include_router(connections.router)
    client = TestClient(app)
    assert client.get("/api/v1/automation/connections").status_code == 403
    user.role = "owner"
    assert client.post("/api/v1/automation/connections", json={
        "provider": "google_docs", "label": "Docs",
    }).status_code == 403
