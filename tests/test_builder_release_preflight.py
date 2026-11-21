"""Release preflight checks every reachable branch for a terminal path."""
from api.simple_builder import Scenario, release_preflight


def check(nodes):
    return release_preflight(Scenario.model_validate({
        "name": "Release preflight", "start": "start", "nodes": nodes,
    }))


def test_simple_complete_flow_is_ready():
    result = check([
        {"id": "start", "kind": "message", "text": "Hello", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert result["ready"]
    assert result["terminal_count"] == 1
    assert result["checks"]["all_reachable_nodes_can_finish"]


def test_missing_terminal_blocks_release():
    result = check([
        {"id": "start", "kind": "message", "text": "Hello"},
    ])
    assert not result["ready"]
    assert {"no_terminal", "no_path_to_end"} <= {
        issue["code"] for issue in result["issues"]
    }


def test_one_branch_with_no_exit_blocks_release():
    result = check([
        {"id": "start", "kind": "choice", "text": "Choose", "options": [
            {"label": "Done", "target": "end"},
            {"label": "Loop", "target": "loop"},
        ]},
        {"id": "loop", "kind": "message", "text": "Again", "next": "loop"},
        {"id": "end", "kind": "end"},
    ])
    assert not result["ready"]
    assert ("loop", "no_path_to_end") in {
        (issue["node_id"], issue["code"]) for issue in result["issues"]
    }


def test_interactive_loop_with_exit_is_allowed():
    result = check([
        {"id": "start", "kind": "choice", "text": "Choose", "options": [
            {"label": "Again", "target": "start"},
            {"label": "Finish", "target": "end"},
        ]},
        {"id": "end", "kind": "end"},
    ])
    assert result["ready"]


def test_unreachable_terminal_does_not_count():
    result = check([
        {"id": "start", "kind": "message", "text": "Hello"},
        {"id": "end", "kind": "end"},
    ])
    assert not result["ready"]
    assert result["terminal_count"] == 0
