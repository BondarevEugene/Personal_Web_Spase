"""Unified workflow reports expose truthful state and export readiness."""
from types import SimpleNamespace

from api.builder_projects import workflow_report
from api.simple_builder import Scenario


def report(nodes):
    scenario = Scenario.model_validate({
        "name": "Workflow", "start": "start", "nodes": nodes,
    })
    project = SimpleNamespace(
        id="00000000-0000-4000-8000-000000000001",
        scenario_json=scenario.model_dump_json(),
        layout_json="{}",
    )
    return workflow_report(scenario, project)


def test_complete_saved_project_has_export_link():
    result = report([
        {"id": "start", "kind": "message", "text": "Hello", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert result["export_available"] is True
    assert result["export_url"].endswith("/export")
    assert result["simulation"]["status"] == "completed"
    assert result["live_deployment_enabled"] is False
    assert len(result["revision"]) == 64


def test_incomplete_project_is_blocked():
    result = report([
        {"id": "start", "kind": "message", "text": "Hello"},
    ])
    assert result["export_available"] is False
    assert result["export_url"] is None
    assert next(x for x in result["stages"] if x["id"] == "export")["status"] == "blocked"


def test_interactive_project_reports_awaiting_input():
    result = report([
        {"id": "start", "kind": "input", "text": "Name?", "variable": "name", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert result["export_available"]
    assert result["simulation"]["status"] == "awaiting_input"
    assert next(x for x in result["stages"] if x["id"] == "deployment")["status"] == "manual"
