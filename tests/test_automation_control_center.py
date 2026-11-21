"""Automation Control Center: ownership and retry safety regression tests."""

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api import automation


class ContextFactory:
    def __init__(self, db=None):
        self.db = db

    def __call__(self):
        db = self.db

        class Context:
            def __enter__(self):
                return db

            def __exit__(self, *_):
                return False

        return Context()


def client(monkeypatch, *, db=None, user=None):
    monkeypatch.setattr(automation, "session_factory", lambda: ContextFactory(db))
    if user is None:
        def reject(request, session):
            raise HTTPException(401, "Sign in")
        monkeypatch.setattr(automation, "require_user", reject)
    else:
        monkeypatch.setattr(automation, "require_user", lambda request, session: user)
        monkeypatch.setattr(automation, "csrf", lambda request: None)
    app = FastAPI()
    app.include_router(automation.router)
    return TestClient(app)


def test_control_summary_requires_authentication(monkeypatch):
    api = client(monkeypatch)
    assert api.get("/api/v1/automation/control/summary").status_code == 401


def test_retry_requires_authentication(monkeypatch):
    api = client(monkeypatch)
    workflow = "00000000-0000-0000-0000-000000000001"
    run = "00000000-0000-0000-0000-000000000002"
    response = api.post(
        f"/api/v1/automation/workflows/{workflow}/runs/{run}/retry-dry-run"
    )
    assert response.status_code == 401


def test_live_retry_is_never_executed(monkeypatch):
    owner = SimpleNamespace(id="customer-1", role="owner")
    monkeypatch.setattr(
        automation, "row_for",
        lambda db, user_id, workflow_id: SimpleNamespace(id=workflow_id),
    )

    class DB:
        def scalar(self, query):
            return SimpleNamespace(mode="live", status="failed", id="run-1")

    api = client(monkeypatch, db=DB(), user=owner)
    monkeypatch.setattr(
        automation, "record_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Live run replay attempted")
        ),
    )
    workflow = "00000000-0000-0000-0000-000000000001"
    run = "00000000-0000-0000-0000-000000000002"
    response = api.post(
        f"/api/v1/automation/workflows/{workflow}/runs/{run}/retry-dry-run"
    )
    assert response.status_code == 409


def test_control_page_and_browser_script_exist():
    root = Path(__file__).resolve().parents[1]
    page = (root / "templates" / "automation_control.html").read_text(
        encoding="utf-8"
    )
    script = (root / "omni_site" / "static" / "automation_control.js").read_text(
        encoding="utf-8"
    )
    assert 'id="control-history"' in page
    assert "retry-dry-run" in script
    assert "connectors/diagnostics" in script
    assert "control-select-workflow" in page
    assert "control-node-diagnostics" in page
    assert "window.confirm" in script


def test_connection_management_ui_wires_real_owner_api():
    root = Path(__file__).resolve().parents[1]
    page = (root / "templates" / "automation_control.html").read_text(encoding="utf-8")
    script = (root / "omni_site" / "static" / "automation_control.js").read_text(encoding="utf-8")
    assert 'id="control-connect-form"' in page
    assert 'id="control-connections"' in page
    assert "oauth/" in script
    assert "/connections" in script
    assert "/health" in script
    assert "/disconnect" in script
    assert "/audit" in script
    assert "X-Omni-CSRF" in script
    assert "window.confirm" in script
    assert "textContent" in script
