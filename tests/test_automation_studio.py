"""The Automation Studio UI must expose real APIs and mounted assets."""
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_studio_mounts_working_assets_and_controls():
    response = client.get("/automation/studio")
    assert response.status_code == 200, response.text
    for text in ('id="auto-canvas"', 'id="auto-inspector-body"',
                 'id="auto-run"', 'id="auto-workflows"', 'id="auto-webhook"',
                 'data-kind="http"', 'data-kind="google_docs"',
                 'data-kind="google_sheets"', 'data-kind="facebook_page"',
                 'data-kind="instagram"', 'data-kind="approval"'):
        assert text in response.text
    js = client.get("/studio-assets/automation_studio.js")
    css = client.get("/studio-assets/automation_studio.css")
    assert js.status_code == css.status_code == 200
    for handler in ("function render()", "function connect(", "saveWorkflow",
                    "runWorkflow", "loadRuns", "webhook"):
        assert handler in js.text
    assert ".auto-canvas" in css.text


def test_home_links_directly_to_automation_studio():
    home = client.get("/")
    assert home.status_code == 200
    assert 'href="/automation/studio"' in home.text


def test_workflow_runtime_and_hook_routes_registered():
    paths = app.openapi()["paths"]
    for path in ("/api/v1/automation/catalog",
                 "/api/v1/automation/workflows",
                 "/api/v1/automation/workflows/{workflow_id}/runs",
                 "/api/v1/automation/workflows/{workflow_id}/webhook",
                 "/hooks/automation/{workflow_id}"):
        assert path in paths
