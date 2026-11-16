"""Smoke contract: Swagger generation and canonical Bot Lab routes."""
from fastapi.testclient import TestClient

from server import app


def test_expected_routes_registered():
    paths={getattr(r,"path","") for r in app.routes}
    for route in ("/architect", "/bots/lab", "/health", "/openapi.json"):
        assert route in paths, f"{route} not registered; check current Python server module"


def test_swagger_document_generated_and_served():
    schema=app.openapi()
    assert schema["openapi"].startswith("3.")
    assert "/api/v1/bot-lab/overview" in schema["paths"]
    with TestClient(app) as client:
        response=client.get("/openapi.json")
        assert response.status_code==200, response.text[:500]
        assert response.json()["paths"]["/api/v1/bot-lab/overview"]


def test_bot_lab_guest_redirects_not_404():
    with TestClient(app) as client:
        r=client.get("/bots/lab",follow_redirects=False)
    assert r.status_code==303, r.text[:300]
    assert r.headers["location"]=="/account/login"


def test_graph_workspace_and_lab_assets():
    with TestClient(app) as client:
        r=client.get("/architect")
        assert r.status_code==200, r.text[:300]
        assert "graph_workspace.css" in r.text
        assert "graph_workspace.js" in r.text
        assert client.get("/studio-assets/graph_workspace.css").status_code==200
        assert client.get("/studio-assets/bot_lab.css").status_code==200
