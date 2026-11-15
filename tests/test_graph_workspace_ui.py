"""Graph Studio workspace UX must not change existing graph editor contract."""
from pathlib import Path

from fastapi.testclient import TestClient
from server import app


def test_workspace_mode_controls_and_bot_lab_navigation():
    client = TestClient(app)
    page = client.get("/architect")
    assert page.status_code == 200
    markup = page.text
    assert 'class="platform-app builder-app graph-workspace-compact"' in markup
    assert 'id="btn-workspace-density"' in markup
    assert 'aria-pressed="true"' in markup
    assert 'id="graph-workspace-help"' in markup
    assert 'href="/bots/lab"' in markup
    assert 'graph_workspace.css' in markup
    assert 'graph_workspace.js' in markup


def test_graph_unchanged_controls_remain_available():
    page = TestClient(app).get("/architect").text
    for control in ("scenario-name", "btn-cloud-save", "cloud-project-list",
                    "btn-validate", "btn-test-canvas", "btn-export",
                    "btn-expand-canvas"):
        assert 'id="' + control + '"' in page
    for node in ("message", "choice", "photo", "document", "input",
                 "condition", "set_variable", "end"):
        assert 'data-add="' + node + '"' in page


def test_workspace_assets_scoped_to_builder_and_no_secret_storage():
    client = TestClient(app)
    css = client.get("/studio-assets/graph_workspace.css")
    js = client.get("/studio-assets/graph_workspace.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert ".builder-app.graph-workspace-compact" in css.text
    assert "@media(max-width:700px)" in css.text
    assert 'button.addEventListener("click"' in js.text
    for unsafe in ("localStorage", "BOT_TOKEN", "OMNI_BOT_VAULT_FERNET_KEY"):
        assert unsafe not in js.text
