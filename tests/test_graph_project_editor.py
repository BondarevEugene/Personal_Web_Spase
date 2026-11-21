"""Graph project editor stays behind authentication."""
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_anonymous_cannot_open_editor():
    response = client.get(
        "/account/graph-project/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 401


def test_editor_asset_is_served():
    response = client.get("/studio-assets/graph_project_editor.js")
    assert response.status_code == 200
    assert 'method: "PUT"' in response.text
    assert 'X-Omni-CSRF' in response.text
    assert "localStorage" not in response.text
