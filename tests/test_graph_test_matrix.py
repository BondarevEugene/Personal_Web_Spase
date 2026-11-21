"""Acceptance tests for Graph Studio's bounded branch matrix and UI integration."""
from pathlib import Path

from api.graph_test_matrix import dialogue_matrix
from api.simple_builder import Scenario

ROOT = Path(__file__).resolve().parents[1]


def graph(nodes):
    return Scenario.model_validate({
        "name": "Тестовый бот",
        "start": "start",
        "nodes": nodes,
    })


def test_choice_matrix_exercises_both_outcomes_and_tracks_edges():
    scenario = graph([
        {"id": "start", "kind": "choice", "text": "Выберите",
         "options": [{"label": "А", "target": "a"}, {"label": "Б", "target": "b"}]},
        {"id": "a", "kind": "end"},
        {"id": "b", "kind": "end"},
    ])
    report = dialogue_matrix(scenario)
    assert report["completed_cases"] == 2
    assert report["coverage_percent"] == 100
    assert {"source": "start", "target": "a"} in report["covered_edges"]
    assert {"source": "start", "target": "b"} in report["covered_edges"]
    assert all(case["trace"] for case in report["cases"])


def test_input_is_filled_synthetically_and_trace_records_variables():
    scenario = graph([
        {"id": "start", "kind": "input", "text": "Имя?",
         "variable": "name", "next": "reply"},
        {"id": "reply", "kind": "message", "text": "Привет, {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    report = dialogue_matrix(scenario)
    assert report["completed_cases"] == 1
    assert report["cases"][-1]["variables"]["name"] == "Тест"
    assert report["cases"][-1]["trace"][1]["text"] == "Привет, Тест"


def test_infinite_automatic_loop_is_bounded():
    scenario = graph([{"id": "start", "kind": "message",
                       "text": "Повтор", "next": "start"}])
    report = dialogue_matrix(scenario)
    assert report["case_count"] == 1
    assert report["cases"][0]["status"] == "step_limit"
    assert report["cases"][0]["steps"] == 50


def test_test_matrix_case_limit_is_explicit():
    scenario = graph([
        {"id": "start", "kind": "choice", "text": "Выберите",
         "options": [{"label": "А", "target": "a"}, {"label": "Б", "target": "b"}]},
        {"id": "a", "kind": "end"},
        {"id": "b", "kind": "end"},
    ])
    report = dialogue_matrix(scenario, max_cases=2)
    assert report["case_count"] == 2
    assert report["truncated"] is True


def test_editor_contains_real_debugger_controls_and_assets():
    html = (ROOT / "templates/builder_pro_final.html").read_text(encoding="utf-8")
    js = (ROOT / "omni_site/static/graph_release_inspector.js").read_text(encoding="utf-8")
    for identifier in ("btn-release-inspect", "release-inspect-issues",
                       "release-inspect-cases", "release-inspect-trace",
                       "release-inspect-variables"):
        assert identifier in html
        assert identifier in js
    assert "/release-evidence" in js
    assert "/test-matrix" in js
    assert "textContent" in js


def test_matrix_distinguishes_unreachable_nodes_from_untested_branches():
    scenario = graph([
        {"id": "start", "kind": "condition", "variable": "flag",
         "operator": "equals", "value": "yes",
         "true_target": "yes", "false_target": "no"},
        {"id": "yes", "kind": "end"},
        {"id": "no", "kind": "end"},
        {"id": "orphan", "kind": "end"},
    ])
    report = dialogue_matrix(scenario)
    assert report["unreachable_nodes"] == ["orphan"]
    assert report["untested_reachable_nodes"] == ["yes"]
    assert report["reachable_edge_count"] == 2
    assert report["covered_edge_count"] == 1
    assert report["edge_coverage_percent"] == 50.0
    assert report["uncovered_edges"] == [{"source": "start", "target": "yes"}]
    assert report["status_counts"] == {"completed": 1}


def test_matrix_identifies_unexercised_choice_option_under_case_limit():
    scenario = graph([
        {"id": "start", "kind": "choice", "text": "Choose",
         "options": [{"label": "A", "target": "a"}, {"label": "B", "target": "b"}]},
        {"id": "a", "kind": "end"},
        {"id": "b", "kind": "end"},
    ])
    report = dialogue_matrix(scenario, max_cases=2)
    assert report["truncated"] is True
    assert report["untested_choice_options"] == [
        {"node_id": "start", "option_index": 1, "target": "b"}
    ]
    assert report["edge_coverage_percent"] == 50.0


def test_matrix_rejects_invalid_case_limits():
    import pytest

    scenario = graph([{"id": "start", "kind": "end"}])
    for limit in (0, -1, 201):
        with pytest.raises(ValueError, match="max_cases"):
            dialogue_matrix(scenario, max_cases=limit)


def test_release_lab_visual_coverage_contract():
    html = (ROOT / "templates/builder_pro_final.html").read_text(encoding="utf-8")
    js = (ROOT / "omni_site/static/graph_release_inspector.js").read_text(encoding="utf-8")
    css = (ROOT / "omni_site/static/graph_release_inspector.css").read_text(encoding="utf-8")
    for identifier in (
        "release-inspect-coverage", "release-inspect-readiness",
        "release-inspect-edges",
    ):
        assert f'id="{identifier}"' in html
        assert f"$('{identifier}')" in js
    for status in ("graph-release-blocker", "graph-release-untested",
                   "graph-release-unreachable"):
        assert status in js
        assert status in css
    assert "matrix.uncovered_edges" in js
    assert "matrix.untested_choice_options" in js
    assert "evidence.export_ready" in js
    assert "evidence.revision !== matrix.revision" in js
    assert "textContent" in js
