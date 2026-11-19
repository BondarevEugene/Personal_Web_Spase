"""Step debugger contracts against the actual Python scenario interpreter."""
from pathlib import Path

from fastapi.testclient import TestClient
from server import app


client = TestClient(app)
BASE = "/api/v1/builder/simple/simulate"
ROOT = Path(__file__).resolve().parents[1]


def sample_scenario():
    return {
        "name": "Debuggable workflow",
        "start": "welcome",
        "nodes": [
            {"id": "welcome", "kind": "message", "text": "Hi", "next": "set"},
            {"id": "set", "kind": "set_variable", "variable": "state",
             "value": "ready", "next": "check"},
            {"id": "check", "kind": "condition", "variable": "state",
             "operator": "equals", "value": "ready",
             "true_target": "ask", "false_target": "fail"},
            {"id": "ask", "kind": "input", "text": "Enter name",
             "variable": "name", "next": "choose"},
            {"id": "choose", "kind": "choice", "text": "Continue?",
             "options": [{"label": "Yes", "target": "finish"},
                         {"label": "No", "target": "fail"}]},
            {"id": "finish", "kind": "end", "text": "Done"},
            {"id": "fail", "kind": "end", "text": "Failed"},
        ],
    }


def test_debug_trace_has_real_before_after_state_and_condition_branch():
    response = client.post(BASE, json={"scenario": sample_scenario()})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "awaiting_input"
    assert body["steps"] == 4
    first, setter, condition, waiting = body["trace"]
    assert first["variables_before"] == {}
    assert first["variables_after"] == {}
    assert first["next"] == "set"
    assert setter["variables_before"] == {}
    assert setter["variables_after"] == {"state": "ready"}
    assert setter["next"] == "check"
    assert condition["result"] is True
    assert condition["next"] == "ask"
    assert condition["variables_after"] == {"state": "ready"}
    assert waiting["next"] is None
    assert waiting["variables_before"] == {"state": "ready"}
    assert body["variables"] == {"state": "ready"}


def test_debugger_records_input_and_selected_choice():
    response = client.post(BASE, json={
        "scenario": sample_scenario(),
        "inputs": {"ask": "Alex"},
        "choices": {"choose": 0},
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["variables"] == {"state": "ready", "name": "Alex"}
    assert [step["id"] for step in body["trace"]] == [
        "welcome", "set", "check", "ask", "choose", "finish"
    ]
    entered = body["trace"][3]
    assert entered["variables_before"] == {"state": "ready"}
    assert entered["variables_after"]["name"] == "Alex"
    assert entered["next"] == "choose"
    choice = body["trace"][4]
    assert choice["selected_option"] == 0
    assert choice["next"] == "finish"


def test_waiting_for_choice_retains_variable_snapshots():
    response = client.post(BASE, json={
        "scenario": sample_scenario(),
        "inputs": {"ask": "Alex"},
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "awaiting_choice"
    assert body["at"] == "choose"
    assert body["trace"][-1]["variables_before"] == {
        "state": "ready", "name": "Alex"
    }
    assert body["trace"][-1]["next"] is None
    assert len(body["options"]) == 2


def test_debugger_is_a_real_trace_ui():
    html = client.get("/architect")
    assert html.status_code == 200
    for marker in (
        'id="debug-step-prev"', 'id="debug-step-next"',
        'id="debug-step-position"', 'id="debug-step-details"',
        'id="preview-trace"',
    ):
        assert marker in html.text
    js = (ROOT / "omni_site" / "static" / "graph_studio.js").read_text(
        encoding="utf-8"
    )
    assert "function showDebugStep(index)" in js
    assert "item.variables_before" in js
    assert "item.variables_after" in js
    assert "item.next" in js
    assert "selected=item.id;inspector();render();" in js
    assert "if(serial!==debugSerial)return;" in js
