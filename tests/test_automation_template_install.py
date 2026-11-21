"""Flagship template installation and connector-readiness contracts."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import automation
from omni_site.automation_flagship import BY_SLUG, template_definition


def test_template_registry_and_install_routes_are_declared():
    routes = {(route.path, tuple(sorted(route.methods or []))) for route in automation.router.routes}
    assert any(path == "/api/v1/automation/templates" for path, _ in routes)
    assert any(path == "/api/v1/automation/templates/{slug}/install" for path, _ in routes)
    assert any(path == "/api/v1/automation/connectors/readiness" for path, _ in routes)


def test_template_graphs_remain_server_owned_and_valid():
    for slug in BY_SLUG:
        graph = template_definition(slug)
        assert graph.start in {node.id for node in graph.nodes}
        assert graph.name
        assert len(graph.nodes) <= 80


def test_install_requires_authentication(monkeypatch):
    def reject_user(request, db):
        from fastapi import HTTPException

        raise HTTPException(401, "Sign in")

    class DummyFactory:
        def __call__(self):
            class Context:
                def __enter__(self):
                    return object()

                def __exit__(self, *args):
                    return False

            return Context()

    monkeypatch.setattr(automation, "session_factory", DummyFactory)
    monkeypatch.setattr(automation, "require_user", reject_user)
    app = FastAPI()
    app.include_router(automation.router)
    client = TestClient(app)
    response = client.post("/api/v1/automation/templates/document-routing/install")
    assert response.status_code == 401
    assert client.get("/api/v1/automation/connectors/readiness").status_code == 401


def test_studio_template_installer_is_present():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    page = (root / "templates" / "automation_studio.html").read_text(encoding="utf-8")
    script = (root / "omni_site" / "static" / "automation_studio.js").read_text(
        encoding="utf-8"
    )
    assert 'id="auto-install-template"' in page
    assert "async function installTemplate()" in script
    assert "encodeURIComponent(slug)+'/install'" in script
