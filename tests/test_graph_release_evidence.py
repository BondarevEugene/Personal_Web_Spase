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
