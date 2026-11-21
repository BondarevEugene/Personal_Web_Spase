"""Advanced Telegram Builder logic nodes: API simulation and exported code."""
import ast
from io import BytesIO
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.simple_builder import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

SCENARIO = {
    "name": "Personalized Telegram bot",
    "start": "ask",
    "nodes": [
        {"id": "ask", "kind": "input", "text": "Как вас зовут?",
         "variable": "name", "next": "greet"},
        {"id": "greet", "kind": "set_variable", "variable": "salutation",
         "value": "Привет, {{name}}", "next": "check"},
        {"id": "check", "kind": "condition", "variable": "name",
         "operator": "equals", "value": "Алексей",
         "true_target": "vip", "false_target": "regular"},
        {"id": "vip", "kind": "message", "text": "Для вас: {{salutation}}", "next": "done"},
        {"id": "regular", "kind": "message", "text": "{{salutation}}", "next": "done"},
        {"id": "done", "kind": "end", "text": "До встречи"},
    ],
}


def trace_ids(response):
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["trace"]]


def test_input_node_pauses_until_text_is_supplied():
    response = client.post("/api/v1/builder/simple/simulate", json={"scenario": SCENARIO})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "awaiting_input"
    assert response.json()["at"] == "ask"


def test_variables_and_conditions_route_both_paths():
    path = "/api/v1/builder/simple/simulate"
    vip = client.post(path, json={"scenario": SCENARIO, "inputs": {"ask": "Алексей"}})
    regular = client.post(path, json={"scenario": SCENARIO, "inputs": {"ask": "Мария"}})
    assert trace_ids(vip) == ["ask", "greet", "check", "vip", "done"]
    assert trace_ids(regular) == ["ask", "greet", "check", "regular", "done"]
    assert vip.json()["variables"]["salutation"] == "Привет, Алексей"
    assert regular.json()["variables"]["salutation"] == "Привет, Мария"
    assert vip.json()["trace"][2]["result"] is True
    assert regular.json()["trace"][2]["result"] is False


def test_missing_condition_branch_and_variable_are_rejected():
    broken = {**SCENARIO, "nodes": [{**node} for node in SCENARIO["nodes"]]}
    broken["nodes"][2]["false_target"] = "does_not_exist"
    assert client.post("/api/v1/builder/simple/validate", json=broken).status_code == 422
    broken["nodes"][2]["false_target"] = ""
    assert client.post("/api/v1/builder/simple/validate", json=broken).status_code == 422
    broken["nodes"][2]["false_target"] = "regular"
    broken["nodes"][0]["variable"] = "not valid!"
    assert client.post("/api/v1/builder/simple/validate", json=broken).status_code == 422


def test_exported_bot_supports_real_variable_input_and_branch_handlers():
    response = client.post("/api/v1/builder/simple/export", json=SCENARIO)
    assert response.status_code == 200, response.text
    with ZipFile(BytesIO(response.content)) as archive:
        source = archive.read("bot.py").decode("utf-8")
        ast.parse(source)
        assert "VALUES:" in source
        assert 'kind == "input"' in source
        assert 'kind == "condition"' in source
        assert 'kind == "set_variable"' in source
        assert "message.from_user.id" in source
        assert "render_text" in source


def test_graph_studio_exposes_logic_nodes_to_editor():
    from server import app as platform
    page = TestClient(platform).get("/architect")
    assert page.status_code == 200
    for kind in ("input", "condition", "set_variable"):
        assert f'data-add="{kind}"' in page.text
    script = TestClient(platform).get("/studio-assets/graph_studio.js")
    assert script.status_code == 200
    for token in ("true_target", "false_target", "set_variable", "serverDryRun"):
        assert token in script.text
