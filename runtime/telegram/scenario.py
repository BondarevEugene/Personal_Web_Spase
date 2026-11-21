"""Standalone, dependency-free scenario validation for runtime and portal."""
from __future__ import annotations
import base64
import json
import re
from typing import Any

SCENARIO_LIMIT = 200_000
BODY_LIMIT = 1_048_576
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
PLACEHOLDER = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")
SUPPORTED = {"message", "choice", "photo", "document", "end",
             "input", "condition", "set_variable"}


def read_scenario(encoded: str) -> dict[str, Any]:
    """Bounded configuration supplied by the trusted deployment worker."""
    if not encoded or len(encoded) > 300_000:
        raise ValueError("Scenario configuration missing or too large")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > SCENARIO_LIMIT:
            raise ValueError("Scenario too large")
        spec = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, TypeError) as exc:
        raise ValueError("Invalid runtime scenario encoding") from exc
    if not isinstance(spec, dict):
        raise ValueError("Scenario must be an object")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 100:
        raise ValueError("Invalid node count")
    table = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Invalid node")
        nid = node.get("id")
        if not isinstance(nid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", nid):
            raise ValueError("Invalid node ID")
        if nid in table or node.get("kind") not in SUPPORTED:
            raise ValueError("Duplicate or unsupported node")
        if len(str(node.get("text") or "")) > 4000:
            raise ValueError("Node text too long")
        table[nid] = node
    if spec.get("start") not in table:
        raise ValueError("Start node not found")
    for node in nodes:
        kind = node["kind"]
        if kind in {"input", "set_variable", "condition"} and not (
            isinstance(node.get("variable"), str) and NAME_PATTERN.fullmatch(node["variable"])
        ):
            raise ValueError("Invalid variable")
        targets = []
        if kind == "choice":
            options = node.get("options")
            if not isinstance(options, list) or not 1 <= len(options) <= 20:
                raise ValueError("Invalid choice list")
            for option in options:
                if not isinstance(option, dict) or not isinstance(option.get("label"), str):
                    raise ValueError("Invalid choice")
                if not 1 <= len(option["label"]) <= 80:
                    raise ValueError("Invalid choice label")
                targets.append(option.get("target"))
        elif kind == "condition":
            if node.get("operator") not in {"equals", "not_equals", "contains", "not_empty"}:
                raise ValueError("Unsupported condition")
            targets += [node.get("true_target"), node.get("false_target")]
        elif kind != "end":
            targets.append(node.get("next"))
        if any(t not in table for t in targets):
            raise ValueError("Missing scenario target")
    return spec


