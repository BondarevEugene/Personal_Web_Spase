"""Bounded Graph Studio test matrix: exercise dialogue branches without Telegram.

Runs only the existing deterministic interpreter; never executes user code.
"""
from __future__ import annotations

from collections import Counter, deque

from api.simple_builder import Scenario, SimulationRequest, simulate_scenario


def dialogue_matrix(scenario: Scenario, *, max_cases: int = 24) -> dict:
    """Explore distinct choice outcomes with bounded breadth-first dry-runs.

    Conditions are data-dependent, so coverage is reported honestly rather than
    claiming exhaustive execution of every possible user input.
    """
    if not 1 <= max_cases <= 200:
        raise ValueError('max_cases must be between 1 and 200')
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
    by_id = {node.id: node for node in scenario.nodes}
    expected_edges = set()
    for node in scenario.nodes:
        if node.next:
            expected_edges.add((node.id, node.next))
        if node.kind == "choice":
            expected_edges.update((node.id, option.target) for option in node.options)
        if node.kind == "condition":
            expected_edges.update(((node.id, node.true_target), (node.id, node.false_target)))
    reachable = set()
    pending = deque([scenario.start])
    while pending:
        current = pending.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(target for source, target in expected_edges if source == current)
    reachable_edges = {(source, target) for source, target in expected_edges if source in reachable}
    status_counts = dict(sorted(Counter(case["status"] for case in cases).items()))
    completed = status_counts.get("completed", 0)
    untested_choices = [
        {"node_id": node.id, "option_index": index, "target": option.target}
        for node in scenario.nodes if node.kind == "choice" and node.id in reachable
        for index, option in enumerate(node.options)
        if not any(
            case["choices"].get(node.id) == index
            and any(row["id"] == node.id for row in case["trace"])
            for case in cases
        )
    ]

    return {
        "cases": cases,
        "case_count": len(cases),
        "completed_cases": completed,
        "status_counts": status_counts,
        "reachable_nodes": sorted(reachable),
        "unreachable_nodes": sorted(all_nodes - reachable),
        "untested_reachable_nodes": sorted(reachable - covered_nodes),
        "reachable_edge_count": len(reachable_edges),
        "covered_edge_count": len(covered_edges & reachable_edges),
        "edge_coverage_percent": round(100 * len(covered_edges & reachable_edges) / len(reachable_edges), 1) if reachable_edges else 100.0,
        "uncovered_edges": [
            {"source": source, "target": target}
            for source, target in sorted(reachable_edges - covered_edges)
        ],
        "untested_choice_options": untested_choices,
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
            "Conditional outcomes depend on synthetic inputs and may remain untested",
            "Unreachable nodes are reported separately from untested reachable nodes",
            "Coverage is not proof of Telegram delivery or production readiness",
        ],
    }
