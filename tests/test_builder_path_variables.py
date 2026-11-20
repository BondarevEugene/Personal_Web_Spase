"""Path-aware variable diagnostics for the Telegram graph builder."""
from api.simple_builder import Scenario, analyze_scenario


def graph(nodes):
    return Scenario.model_validate({"name": "Path validation", "start": "start", "nodes": nodes})


def codes(scenario):
    return {(item["node_id"], item["code"]) for item in analyze_scenario(scenario)["issues"]}


def test_variable_initialized_on_every_branch():
    scenario = graph([
        {"id": "start", "kind": "choice", "text": "Choose", "options": [
            {"label": "A", "target": "setA"}, {"label": "B", "target": "setB"}]},
        {"id": "setA", "kind": "set_variable", "variable": "name", "value": "A", "next": "join"},
        {"id": "setB", "kind": "set_variable", "variable": "name", "value": "B", "next": "join"},
        {"id": "join", "kind": "message", "text": "Hi {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert ("join", "variable_may_be_unset") not in codes(scenario)


def test_variable_missing_on_one_branch():
    scenario = graph([
        {"id": "start", "kind": "choice", "text": "Choose", "options": [
            {"label": "A", "target": "setA"}, {"label": "B", "target": "skip"}]},
        {"id": "setA", "kind": "set_variable", "variable": "name", "value": "A", "next": "join"},
        {"id": "skip", "kind": "message", "text": "Skip", "next": "join"},
        {"id": "join", "kind": "message", "text": "Hi {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert ("join", "variable_may_be_unset") in codes(scenario)


def test_set_variable_reads_old_value_before_assignment():
    scenario = graph([
        {"id": "start", "kind": "set_variable", "variable": "name",
         "value": "Hello {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert ("start", "variable_may_be_unset") in codes(scenario)


def test_condition_value_references_are_checked():
    scenario = graph([
        {"id": "start", "kind": "condition", "variable": "name",
         "value": "{{unknown}}", "true_target": "endA", "false_target": "endB"},
        {"id": "endA", "kind": "end"},
        {"id": "endB", "kind": "end"},
    ])
    assert ("start", "undefined_variable") in codes(scenario)
