"""Graph Studio release evidence: topology, blockers and honest readiness."""
from api.graph_release_evidence import graph_inventory, release_evidence
from api.simple_builder import Scenario


def scenario(nodes):
    return Scenario.model_validate({
        "name": "Test bot",
        "start": "start",
        "nodes": nodes,
    })


def test_valid_chain_has_traceable_evidence():
    graph = scenario([
        {"id": "start", "kind": "message", "text": "Hello", "next": "done"},
        {"id": "done", "kind": "end"},
    ])
    result = release_evidence(graph, "project", "revision")
    assert result["inventory"]["reachable_count"] == 2
    assert result["inventory"]["terminal_nodes"] == ["done"]
    assert result["export_ready"] is True
    assert result["live_deployment_verified"] is False
    assert result["revision"] == "revision"


def test_unreachable_nodes_are_reported():
    graph = scenario([
        {"id": "start", "kind": "message", "text": "Hello", "next": "done"},
        {"id": "done", "kind": "end"},
        {"id": "orphan", "kind": "end"},
    ])
    assert graph_inventory(graph)["unreachable_nodes"] == ["orphan"]


def test_missing_terminal_is_blocked():
    graph = scenario([
        {"id": "start", "kind": "message", "text": "Loop", "next": "start"},
    ])
    result = release_evidence(graph, "project", "revision")
    assert result["export_ready"] is False
    assert result["next_action"] == "fix_graph_and_save_revision"
    assert result["blockers"]


def test_branch_edges_are_typed():
    graph = scenario([
        {"id": "start", "kind": "condition", "variable": "name",
         "true_target": "yes", "false_target": "no"},
        {"id": "yes", "kind": "end"},
        {"id": "no", "kind": "end"},
    ])
    edges = graph_inventory(graph)["edges"]
    assert {edge["kind"] for edge in edges} == {"true", "false"}


def test_release_center_contract_and_ui():
    from pathlib import Path

    from api.builder_projects import saved_graph_release_center

    root = Path(__file__).resolve().parents[1]
    html = (root / "templates/builder_pro_final.html").read_text(encoding="utf-8")
    js = (root / "omni_site/static/graph_release_center.js").read_text(encoding="utf-8")
    css = (root / "omni_site/static/graph_release_center.css").read_text(encoding="utf-8")
    assert saved_graph_release_center.__name__ == "saved_graph_release_center"
    for identifier in ("release-center-check", "release-center-status",
                       "release-center-steps", "release-center-download"):
        assert f'id="{identifier}"' in html
        assert f"$('{identifier}')" in js
    assert "/release-center" in js
    assert "report.export_ready" in js
    assert "report.export_url === expected" in js
    assert "textContent" in js
    assert "graph-release-center-blocked" in css


def test_deployment_plan_requires_revision_and_release_preflight():
    import pytest
    from pydantic import ValidationError

    from api.builder_projects import GraphDeploymentRequest

    with pytest.raises(ValidationError):
        GraphDeploymentRequest(name="Demo", max_monthly_usd=10)
    payload = GraphDeploymentRequest(
        revision="a" * 64, name="Demo", max_monthly_usd=10,
    )
    assert payload.transport == "worker"
    assert payload.revision == "a" * 64


def test_release_center_plan_ui_contract():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    html = (root / "templates/builder_pro_final.html").read_text(encoding="utf-8")
    js = (root / "omni_site/static/graph_release_center.js").read_text(encoding="utf-8")
    for identifier in ("release-plan-form", "release-plan-status",
                       "release-plan-history", "release-plan-name",
                       "release-plan-budget"):
        assert f'id="{identifier}"' in html
        assert f"$('{identifier}')" in js
    assert "X-Omni-CSRF" in js
    assert "current.revision" in js
    assert "/deployment-plan" in js
    assert "/api/v1/builder/operations/" in js
    assert "planForm.hidden = !report.export_ready" in js
