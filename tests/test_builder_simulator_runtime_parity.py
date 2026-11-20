"""Simulator must mirror generated Telegram runtime for supported text flows."""
import pytest

from api.simple_builder import SimulationRequest, simulate_scenario


def run(nodes, *, inputs=None, choices=None):
    return simulate_scenario(SimulationRequest.model_validate({
        "scenario": {"name": "Runtime parity", "start": "start", "nodes": nodes},
        "inputs": inputs or {}, "choices": choices or {},
    }))


def test_simulator_renders_assigned_variable():
    result = run([
        {"id": "start", "kind": "set_variable", "variable": "name",
         "value": "Анна", "next": "greet"},
        {"id": "greet", "kind": "message", "text": "Привет, {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ])
    assert result["status"] == "completed"
    assert result["trace"][1]["text"] == "Привет, Анна"


def test_simulator_renders_input_variable():
    result = run([
        {"id": "start", "kind": "input", "text": "Ваше имя?", "variable": "name", "next": "greet"},
        {"id": "greet", "kind": "message", "text": "Привет, {{name}}", "next": "end"},
        {"id": "end", "kind": "end"},
    ], inputs={"start": "Олег"})
    assert result["trace"][1]["text"] == "Привет, Олег"


@pytest.mark.parametrize("value", ["", "   ", "x" * 301])
def test_simulator_rejects_input_rejected_by_bot(value):
    result = run([
        {"id": "start", "kind": "input", "text": "Имя?", "variable": "name", "next": "end"},
        {"id": "end", "kind": "end"},
    ], inputs={"start": value})
    assert result["status"] == "invalid_input"
    assert result["at"] == "start"
    assert "name" not in result["variables"]


def test_simulator_condition_uses_interpolated_value():
    result = run([
        {"id": "start", "kind": "set_variable", "variable": "expected",
         "value": "yes", "next": "answer"},
        {"id": "answer", "kind": "set_variable", "variable": "actual",
         "value": "yes", "next": "check"},
        {"id": "check", "kind": "condition", "variable": "actual",
         "value": "{{expected}}", "true_target": "ok", "false_target": "fail"},
        {"id": "ok", "kind": "end", "text": "Correct"},
        {"id": "fail", "kind": "end", "text": "Wrong"},
    ])
    assert result["trace"][-1]["id"] == "ok"
