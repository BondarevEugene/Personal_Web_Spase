"""Validates actual builder API and generated ZIP without Telegram or Docker."""
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)
SCENARIO = {
    "name": "Demo Telegram bot",
    "start": "welcome",
    "nodes": [
        {"id": "welcome", "kind": "message", "text": "Добро пожаловать!", "next": "choice"},
        {"id": "choice", "kind": "choice", "text": "Что сделать?", "options": [
            {"label": "Информация", "target": "info"},
            {"label": "Завершить", "target": "finish"},
        ]},
        {"id": "info", "kind": "message", "text": "Информация", "next": "finish"},
        {"id": "finish", "kind": "end", "text": "Спасибо"},
    ],
}


def test_builder_api_capabilities():
    r = client.get("/api/v1/builder/simple/capabilities")
    assert r.status_code == 200
    assert r.json()["live_deployment"] is False


def test_validate_real_graph():
    r = client.post("/api/v1/builder/simple/validate", json=SCENARIO)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert r.json()["reachable"] == 4


def test_validation_rejects_missing_targets():
    scenario = dict(SCENARIO)
    scenario["nodes"] = [dict(SCENARIO["nodes"][0], next="missing")] + SCENARIO["nodes"][1:]
    r = client.post("/api/v1/builder/simple/validate", json=scenario)
    assert r.status_code == 422


def test_validation_rejects_empty_choice():
    scenario = dict(SCENARIO)
    nodes = list(SCENARIO["nodes"])
    nodes[1] = dict(nodes[1], options=[])
    scenario["nodes"] = nodes
    assert client.post("/api/v1/builder/simple/validate", json=scenario).status_code == 422


def test_export_contains_compilable_source_and_no_secrets():
    r = client.post("/api/v1/builder/simple/export", json=SCENARIO)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/zip")
    with ZipFile(BytesIO(r.content)) as archive:
        assert set(archive.namelist()) == {
            "scenario.json", "bot.py", "requirements.txt", ".env.example", "README.md"
        }
        source = archive.read("bot.py").decode()
        compile(source, "bot.py", "exec")
        assert "BOT_TOKEN" in source
        assert "12345:REAL" not in source
        assert "Добро пожаловать!" not in source
        assert "Добро пожаловать!" in archive.read("scenario.json").decode()


def test_export_rejects_code_injection_as_node_id():
    scenario = dict(SCENARIO)
    nodes = list(SCENARIO["nodes"])
    nodes[0] = dict(nodes[0], id="welcome;import os")
    scenario["nodes"] = nodes
    assert client.post("/api/v1/builder/simple/export", json=scenario).status_code == 422


def test_builder_page_loads_new_ui():
    response = client.get("/builder_pro_final.html")
    assert response.status_code == 200
    assert "/studio-assets/graph_studio.js?v=5" in response.text
    assert "/studio-assets/builder.js" not in response.text
    assert "/studio-assets/site.css?v=3" in response.text
