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
    assert "/studio-assets/graph_studio.js?v=3" in response.text
    assert "/studio-assets/builder.css?v=3" in response.text
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
