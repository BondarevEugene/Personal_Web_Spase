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
    assert "/studio-assets/graph_studio.js?v=8" in response.text
    assert "/studio-assets/builder.js" not in response.text
    assert "/studio-assets/site.css?v=3" in response.text


def test_simulation_pauses_then_completes_selected_branch():
    url = "/api/v1/builder/simple/simulate"
    first = client.post(url, json={"scenario": SCENARIO})
    assert first.status_code == 200, first.text
    data = first.json()
    assert data["status"] == "awaiting_choice"
    assert [n["id"] for n in data["trace"]] == ["welcome", "choice"]
    assert [x["label"] for x in data["options"]] == ["Информация", "Завершить"]

    second = client.post(url, json={"scenario": SCENARIO, "choices": {"choice": 0}})
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "completed"
    assert [n["id"] for n in second.json()["trace"]] == ["welcome", "choice", "info", "finish"]

    other = client.post(url, json={"scenario": SCENARIO, "choices": {"choice": 1}})
    assert other.status_code == 200
    assert [n["id"] for n in other.json()["trace"]] == ["welcome", "choice", "finish"]


def test_simulation_invalid_selection_and_cycles_are_bounded():
    url = "/api/v1/builder/simple/simulate"
    invalid = client.post(url, json={"scenario": SCENARIO, "choices": {"choice": 19}})
    assert invalid.status_code == 200
    assert invalid.json()["status"] == "invalid_choice"

    cyclic = {"name": "Cyclic example", "start": "loop",
              "nodes": [{"id": "loop", "kind": "message", "text": "again", "next": "loop"}]}
    result = client.post(url, json={"scenario": cyclic})
    assert result.status_code == 200
    assert result.json()["status"] == "step_limit"
    assert result.json()["steps"] == 50


def test_starter_template_catalog_generates_valid_graphs():
    root = "/api/v1/builder/simple"
    response = client.get(root + "/templates")
    assert response.status_code == 200
    templates = response.json()["templates"]
    assert {entry["id"] for entry in templates} == {"info", "faq", "survey"}
    for entry in templates:
        template = client.get(root + "/templates/" + entry["id"])
        assert template.status_code == 200, template.text
        scenario = template.json()["scenario"]
        assert len(scenario["nodes"]) >= 3
        verified = client.post(root + "/validate", json=scenario)
        assert verified.status_code == 200, verified.text
        assert verified.json()["warnings"] == []
        archive = client.post(root + "/export", json=scenario)
        assert archive.status_code == 200, archive.text
        with ZipFile(BytesIO(archive.content)) as packed:
            assert "bot.py" in packed.namelist()
    assert client.get(root + "/templates/not-found").status_code == 404


def test_template_selector_is_wired_to_builder():
    page = client.get("/architect")
    assert page.status_code == 200
    assert 'id="builder-template"' in page.text
    assert 'id="btn-use-template"' in page.text
    script = client.get("/studio-assets/graph_studio.js")
    assert script.status_code == 200
    assert "loadTemplateCatalog" in script.text
    assert "applyStarterTemplate" in script.text
    assert "replaceScenario(()=>result.scenario)" in script.text
