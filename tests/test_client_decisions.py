"""Decision inbox regressions."""
from pathlib import Path

from fastapi.testclient import TestClient

from portal.client_decisions import pending_decisions
from server import app


def test_empty_org_has_no_pending_decisions():
    class EmptySession:
        def scalars(self, statement):
            return self

        def all(self):
            return []

    assert pending_decisions(EmptySession(), "empty-org") == []


def test_anonymous_decisions_redirect():
    response = TestClient(app).get("/account/decisions", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/account/login"


def test_decisions_are_linked_from_workspace():
    root = Path(__file__).resolve().parents[1]
    workspace = (root / "portal/templates/client_workspace_center.html").read_text(
        encoding="utf-8"
    )
    assert "/account/decisions" in workspace
    page = (root / "portal/templates/client_decisions.html").read_text(
        encoding="utf-8"
    )
    assert "decision.project.id" in page
    assert 'user.role != "owner"' in page
