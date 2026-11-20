"""Customer command center regression tests."""
from pathlib import Path

from fastapi.testclient import TestClient

from portal.workspace_center import project_pulses
from server import app


def test_empty_project_collection_has_no_database_queries():
    class NoQueries:
        def execute(self, *args, **kwargs):
            raise AssertionError("unexpected query")

        def scalars(self, *args, **kwargs):
            raise AssertionError("unexpected query")

    assert project_pulses(NoQueries(), [], "org-id") == []


def test_anonymous_workspace_redirects_to_login():
    response = TestClient(app).get("/account/workspace", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/account/login"


def test_command_center_contracts_are_visible():
    root = Path(__file__).resolve().parents[1]
    html = (root / "portal/templates/client_workspace_center.html").read_text(
        encoding="utf-8"
    )
    assert "pulse.percent" in html
    assert "pulse.spec_approved" in html
    assert "pulse.requires_action" in html
    assert "pulse.project.id" in html
    assert "/account/notifications" in html
    assert "/account/projects" in html
    assert 'aria-current="page"' in html
    nav = (root / "portal/templates/_workspace_nav.html").read_text(
        encoding="utf-8"
    )
    assert "/account/workspace" in nav
