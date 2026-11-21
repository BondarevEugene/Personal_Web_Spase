"""Provider diagnostics never leak tokens and never infer Meta permissions."""
import json

from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from automation import connection_health
from automation.connection_vault import seal
from portal.db import Base
from portal.models import AutomationConnection, AutomationCredential


def test_probe_google_scopes(monkeypatch):
    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"scope": "https://www.googleapis.com/auth/spreadsheets"}

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url, params):
            assert url == connection_health.GOOGLE_TOKENINFO
            assert params["access_token"] == "private"
            return Response()

    monkeypatch.setattr(connection_health.httpx, "Client", Client)
    assert connection_health.probe("google_sheets", "private") == {
        "health": "healthy", "permissions_verified": True}
    assert connection_health.probe("google_docs", "private") == {
        "health": "missing_permissions", "permissions_verified": False}


def test_meta_identity_is_not_permission_verification(monkeypatch):
    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "123"}

    class Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url, params):
            assert url == connection_health.META_ME
            return Response()

    monkeypatch.setattr(connection_health.httpx, "Client", Client)
    assert connection_health.probe("instagram", "private") == {
        "health": "authorized_unverified", "permissions_verified": False}


def test_tenant_scoped_vault_probe(monkeypatch):
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", Fernet.generate_key().decode())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        connection = AutomationConnection(
            customer_id="00000000-0000-0000-0000-000000000001",
            provider="google_sheets", label="Analytics",
            status="authorized_unverified")
        db.add(connection)
        db.flush()
        db.add(AutomationCredential(
            connection_id=connection.id, customer_id=connection.customer_id,
            ciphertext=seal(json.dumps({"access_token": "private"})).ciphertext))
        db.commit()
        monkeypatch.setattr(connection_health, "probe",
                            lambda provider, token: {
                                "health": "healthy" if token == "private" else "error",
                                "permissions_verified": True})
        assert connection_health.check_connection(db, connection)["health"] == "healthy"
        connection.status = "disconnected"
        assert connection_health.check_connection(db, connection)["health"] == "disconnected"
