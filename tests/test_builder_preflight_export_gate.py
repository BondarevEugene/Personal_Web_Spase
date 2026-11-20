"""Export release gate applies to direct and saved-project exports."""
import pytest
from fastapi import HTTPException

from api.simple_builder import Scenario, export_scenario


def scenario(nodes):
    return Scenario.model_validate({
        "name": "Release gate", "start": "start", "nodes": nodes,
    })


def test_export_accepts_complete_graph():
    response = export_scenario(scenario([
        {"id": "start", "kind": "message", "text": "Hello", "next": "end"},
        {"id": "end", "kind": "end"},
    ]))
    assert response.media_type == "application/zip"


def test_export_rejects_graph_without_end():
    with pytest.raises(HTTPException) as error:
        export_scenario(scenario([
            {"id": "start", "kind": "message", "text": "Hello"},
        ]))
    assert error.value.status_code == 422
    assert error.value.detail["code"] == "RELEASE_PREFLIGHT_FAILED"
    assert any(item["code"] == "no_terminal" for item in error.value.detail["issues"])


def test_export_rejects_branch_without_exit():
    with pytest.raises(HTTPException) as error:
        export_scenario(scenario([
            {"id": "start", "kind": "choice", "text": "Choose", "options": [
                {"label": "Done", "target": "end"},
                {"label": "Loop", "target": "loop"},
            ]},
            {"id": "loop", "kind": "message", "text": "Again", "next": "loop"},
            {"id": "end", "kind": "end"},
        ]))
    assert error.value.status_code == 422
    assert any(item["code"] == "no_path_to_end" for item in error.value.detail["issues"])


def test_export_allows_interactive_repeat_with_exit():
    response = export_scenario(scenario([
        {"id": "start", "kind": "choice", "text": "Choose", "options": [
            {"label": "Again", "target": "start"},
            {"label": "Finish", "target": "end"},
        ]},
        {"id": "end", "kind": "end"},
    ]))
    assert response.media_type == "application/zip"
