"""Contract checks for the freeform Graph Studio page.

These tests are deliberately independent of running a browser: live pointer and
connector interactions must additionally be smoke-tested in Chrome/Edge.
"""
from pathlib import Path

from fastapi.testclient import TestClient
from server import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_graph_studio_page_loads_premium_shell():
    response = client.get("/architect")
    assert response.status_code == 200
    assert "/studio-assets/graph_studio.js?v=8" in response.text
    assert "/studio-assets/builder.css?v=8" in response.text
    assert 'class="builder-footer"' in response.text
    assert "GRAPH CANVAS" in response.text


def test_graph_assets_are_served():
    for path in ("/studio-assets/graph_studio.js", "/studio-assets/builder.css"):
        result = client.get(path)
        assert result.status_code == 200, path


def test_graph_editor_has_connection_and_export_handlers():
    js = (ROOT / "omni_site/static/graph_studio.js").read_text(encoding="utf-8")
    for feature in ("pointerdown", "pointermove", "dragover", "flow-edges",
                    "connect(target)", "setZoom", "localStorage",
                    "/validate", "/export", "btn-import", "btn-download-json"):
        assert feature in js, feature


def test_graph_export_api_is_unchanged():
    result = client.get("/api/v1/builder/simple/capabilities")
    assert result.status_code == 200
    assert result.json()["export"] == "aiogram 3 Python project ZIP"


def test_integration_catalog_does_not_claim_unimplemented_execution():
    response = client.get("/api/v1/builder/simple/integrations")
    assert response.status_code == 200
    integrations = {item["id"]: item for item in response.json()["integrations"]}
    assert integrations["telegram"]["status"] == "export"
    for name in ("google_docs", "google_sheets", "facebook", "instagram", "http", "python"):
        assert integrations[name]["status"] == "planned"
    capabilities = client.get("/api/v1/builder/simple/capabilities").json()
    assert "python" not in capabilities["supported_blocks"]
    assert capabilities["server_persistence"] is False


def test_palette_distinguishes_real_and_planned_integrations():
    page = client.get("/architect").text
    for name in ("google_docs", "google_sheets", "facebook", "instagram", "http", "python"):
        assert f'data-integration="{name}"' in page
    for kind in ("message", "choice", "photo", "document", "end"):
        assert f'data-add="{kind}"' in page
    js = client.get("/studio-assets/graph_studio.js").text
    assert "integrationDetails" in js
    css = client.get("/studio-assets/builder.css").text
    assert ".node-kind-choice" in css
    assert ".node-kind-end" in css


def test_canvas_has_semantic_node_legend_and_distinct_shapes():
    response = client.get("/architect")
    assert response.status_code == 200
    for kind in ("message", "choice", "photo", "document", "end"):
        assert "legend-" + kind in response.text
    stylesheet = client.get("/studio-assets/builder.css").text
    assert ".graph-legend" in stylesheet
    assert ".node-kind-choice .graph-kind-icon" in stylesheet
    assert ".node-kind-end .graph-kind-icon" in stylesheet

def test_graph_studio_workspace_has_context_menu_fullscreen_and_test_controls():
    page = client.get("/architect").text
    for control in ('id="graph-context-menu"', 'id="btn-expand-canvas"',
                    'id="btn-test-canvas"', 'id="btn-export-info"',
                    'id="preview-trace"', 'id="export-explainer"'):
        assert control in page
    css = client.get("/studio-assets/builder.css").text
    for selector in (".graph-fullscreen", ".graph-context-menu",
                     ".preview-trace", ".export-explainer"):
        assert selector in css
    js = client.get("/studio-assets/graph_studio.js").text
    for handler in ("contextmenu", "duplicateNode", "setExpanded",
                    "preview-trace", "removeNode", "btn-export-info"):
        assert handler in js


def test_workflow_creation_controls_and_backup_present():
    page = client.get("/architect").text
    assert 'id="btn-new-scenario"' in page
    assert 'id="btn-demo-scenario"' in page
    assert 'class="builder-guide"' in page
    script = client.get("/studio-assets/graph_studio.js").text
    for name in ("BACKUP_STORE", "replaceScenario", "const fresh=", "btn-new-scenario",
                 "btn-demo-scenario", "serverDryRun"):
        assert name in script
