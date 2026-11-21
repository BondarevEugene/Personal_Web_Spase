"""Bounded Graph Studio test matrix: exercise dialogue branches without Telegram.

Runs only the existing deterministic interpreter; never executes user code.
"""
from __future__ import annotations

from collections import deque

from api.simple_builder import Scenario, SimulationRequest, simulate_scenario


def dialogue_matrix(scenario: Scenario, *, max_cases: int = 24) -> dict:
    """Explore distinct choice outcomes with bounded breadth-first dry-runs.

    Conditions are data-dependent, so coverage is reported honestly rather than
    claiming exhaustive execution of every possible user input.
    """
    choices: dict[str, int] = {}
    inputs: dict[str, str] = {}
    queue = deque([(choices, inputs)])
    visited = set()
    cases = []
    covered_nodes = set()
    covered_edges = set()
    total_choices = {
        node.id: len(node.options) for node in scenario.nodes if node.kind == "choice"
    }
    while queue and len(cases) < max_cases:
        selected, entered = queue.popleft()
        signature = (tuple(sorted(selected.items())), tuple(sorted(entered.items())))
        if signature in visited:
            continue
        visited.add(signature)
        result = simulate_scenario(SimulationRequest(
            scenario=scenario, choices=selected, inputs=entered,
        ))
        trace = result["trace"]
        covered_nodes.update(row["id"] for row in trace)
        covered_edges.update(
            (row["id"], row["next"]) for row in trace if row.get("next")
        )
        case = {
            "number": len(cases) + 1,
            "status": result["status"],
            "steps": result["steps"],
            "path": [row["id"] for row in trace],
            "choices": dict(selected),
            "inputs": dict(entered),
            "variables": result["variables"],
            "trace": trace,
        }
        cases.append(case)
        if result["status"] == "awaiting_choice":
            node_id = result["at"]
            for index in range(total_choices[node_id]):
                queue.append((dict(selected, **{node_id: index}), dict(entered)))
        elif result["status"] == "awaiting_input":
            node_id = result["at"]
            queue.append((dict(selected), dict(entered, **{node_id: "Тест"})))
    all_nodes = {node.id for node in scenario.nodes}
    completed = sum(case["status"] == "completed" for case in cases)
    return {
        "cases": cases,
        "case_count": len(cases),
        "completed_cases": completed,
        "covered_nodes": sorted(covered_nodes),
        "uncovered_nodes": sorted(all_nodes - covered_nodes),
        "covered_edges": [
            {"source": source, "target": target}
            for source, target in sorted(covered_edges)
        ],
        "coverage_percent": round(100 * len(covered_nodes) / len(all_nodes), 1),
        "truncated": bool(queue),
        "max_cases": max_cases,
        "limitations": [
            "Input values are synthetic; condition branches are not exhaustive",
            "Coverage is not proof of Telegram delivery or production readiness",
        ],
    }
