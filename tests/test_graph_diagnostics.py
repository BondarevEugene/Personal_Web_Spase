"""Graph Studio diagnostics are executable contracts, not decoration."""
from pathlib import Path

from fastapi.testclient import TestClient

from server import app


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/v1/builder/simple"


def scenario(*nodes, start="start"):
    return {"name": "Diagnostic test bot", "start": start, "nodes": list(nodes)}


def test_unreachable_blocks_are_warnings_not_export_errors():
    data = scenario(
        {"id": "start", "kind": "message", "text": "Start", "next": "finish"},
        {"id": "finish", "kind": "end", "text": "Done"},
        {"id": "unused", "kind": "message", "text": "Unused", "next": "finish"},
    )
    result = client.post(BASE + "/validate", json=data)
    assert result.status_code == 200
    body = result.json()
    assert body["ok"] is True
    assert body["reachable"] == 2
    assert any(i["code"] == "unreachable" and i["node_id"] == "unused"
               for i in body["issues"])


def test_dangling_message_is_actionable_error_and_blocks_export():
    data = scenario({"id": "start", "kind": "message", "text": "Hello"})
    result = client.post(BASE + "/validate", json=data)
    assert result.status_code == 200
    body = result.json()
    assert body["ok"] is False
    assert body["error_count"] == 1
    assert body["issues"][0]["code"] == "dead_end"
    exported = client.post(BASE + "/export", json=data)
    assert exported.status_code == 422
    assert exported.json()["detail"]["issues"][0]["code"] == "dead_end"


def test_undefined_template_variable_warns_without_faking_value():
    data = scenario(
        {"id": "start", "kind": "message", "text": "Привет, {{customer}}",
         "next": "finish"},
        {"id": "finish", "kind": "end", "text": "Done"},
    )
    result = client.post(BASE + "/validate", json=data)
    assert result.status_code == 200
    body = result.json()
    assert body["ok"] is True
    assert any(issue["code"] == "undefined_variable"
               and issue["node_id"] == "start" for issue in body["issues"])


def test_automatic_cycle_fails_and_interactive_cycle_is_not_false_positive():
    looping = scenario(
        {"id": "start", "kind": "message", "text": "Again", "next": "start"},
    )
    result = client.post(BASE + "/validate", json=looping)
    assert result.status_code == 200
    assert any(i["code"] == "automatic_cycle" for i in result.json()["issues"])
    assert result.json()["ok"] is False

    interactive = scenario(
        {"id": "start", "kind": "input", "text": "Your name?",
         "variable": "name", "next": "message"},
        {"id": "message", "kind": "message", "text": "Hi, {{name}}",
         "next": "start"},
    )
    result = client.post(BASE + "/validate", json=interactive)
    assert result.status_code == 200
    assert result.json()["ok"] is True
    assert not any(i["code"] == "automatic_cycle" for i in result.json()["issues"])


def test_graph_page_has_real_diagnostics_controls():
    page = client.get("/architect")
    assert page.status_code == 200
    for marker in ('id="graph-diagnostics"', 'id="graph-diagnostics-list"',
                   'id="graph-diagnostics-close"', 'id="btn-validate"'):
        assert marker in page.text
    js = (ROOT / "omni_site" / "static" / "graph_studio.js").read_text(
        encoding="utf-8"
    )
    assert "function showDiagnostics(result)" in js
    assert "graph-diagnostic-error" in js
    assert "scrollIntoView" in js
