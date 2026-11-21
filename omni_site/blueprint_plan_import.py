"""Read-only validation and preview for an imported Blueprint JSON plan.

Import never persists, executes, connects integrations or creates a workflow.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

MAX_BYTES = 256_000
SECTIONS = ("architecture", "milestones", "verification", "risks")
SCHEMAS = {
    "architecture": "omnifactory.blueprint.architecture.v1",
    "milestones": "omnifactory.blueprint.milestones.v1",
    "verification": "omnifactory.blueprint.verification.v1",
    "risks": "omnifactory.blueprint.risks.v1",
}


class PlanValidationError(ValueError):
    """Invalid or incompatible Blueprint plan."""


@dataclass(frozen=True)
class PlanPreview:
    revision: str
    components: int
    connections: int
    milestones: int
    checks: int
    risks: int
    integrations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "omnifactory.blueprint.preview.v1",
            "status": "validated_not_imported",
            "executable": False,
            "revision": self.revision,
            "components": self.components,
            "connections": self.connections,
            "milestones": self.milestones,
            "checks": self.checks,
            "risks": self.risks,
            "integrations": list(self.integrations),
        }


def _objects(value: Any, label: str, limit: int = 100) -> list[dict]:
    if not isinstance(value, list) or len(value) > limit:
        raise PlanValidationError(f"Invalid {label}")
    if not all(isinstance(item, dict) for item in value):
        raise PlanValidationError(f"Invalid {label} item")
    return value


def _ids(items: list[dict], label: str) -> set[str]:
    values = [item.get("id") for item in items]
    if any(not isinstance(value, str) or not value or len(value) > 128 for value in values):
        raise PlanValidationError(f"Invalid {label} ID")
    if len(values) != len(set(values)):
        raise PlanValidationError(f"Duplicate {label} ID")
    return set(values)


def validate_plan(content: bytes) -> PlanPreview:
    if not content or len(content) > MAX_BYTES:
        raise PlanValidationError("Plan must be between 1 and 256000 bytes")
    try:
        plan = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PlanValidationError("Invalid UTF-8 JSON") from exc
    if not isinstance(plan, dict) or plan.get("schema") != "omnifactory.blueprint.plan.v1":
        raise PlanValidationError("Unsupported Blueprint plan schema")
    revision = plan.get("revision")
    if not isinstance(revision, str) or len(revision) != 12 or any(
        c not in "0123456789abcdef" for c in revision
    ):
        raise PlanValidationError("Invalid plan revision")
    if plan.get("deployable") is not False or plan.get("status") != "draft":
        raise PlanValidationError("Only non-deployable draft plans can be previewed")
    for section in SECTIONS:
        value = plan.get(section)
        if not isinstance(value, dict) or value.get("schema") != SCHEMAS[section]:
            raise PlanValidationError(f"Invalid {section} schema")
        if value.get("revision") != revision:
            raise PlanValidationError(f"Revision mismatch: {section}")
    architecture = plan["architecture"]
    if architecture.get("deployable") is not False or architecture.get("status") != "proposed":
        raise PlanValidationError("Architecture must be a non-deployable proposal")
    nodes = _objects(architecture.get("nodes"), "nodes")
    links = _objects(architecture.get("links"), "links", 200)
    integrations = _objects(architecture.get("integrations"), "integrations", 20)
    node_ids = _ids(nodes, "node")
    _ids(integrations, "integration")
    for node in nodes:
        if node.get("type") != "component" or not isinstance(node.get("label"), str):
            raise PlanValidationError("Invalid architecture node")
    for link in links:
        if (
            link.get("source") not in node_ids
            or link.get("target") not in node_ids
            or link.get("source") == link.get("target")
        ):
            raise PlanValidationError("Broken architecture connection")
    if any(item.get("connected") is not False for item in integrations):
        raise PlanValidationError("Connected integrations are not accepted")
    milestones = _objects(plan["milestones"].get("items"), "milestones")
    milestone_ids = _ids(milestones, "milestone")
    for item in milestones:
        deps = item.get("depends_on")
        if not isinstance(deps, list) or any(
            not isinstance(dep, str) or dep not in milestone_ids or dep == item["id"]
            for dep in deps
        ):
            raise PlanValidationError("Invalid milestone dependency")
        if item.get("status") != "proposed":
            raise PlanValidationError("Unexpected milestone state")
    checks = _objects(plan["verification"].get("checks"), "checks")
    _ids(checks, "check")
    if plan["verification"].get("status") != "not_executed" or any(
        item.get("result") != "not_run" for item in checks
    ):
        raise PlanValidationError("Executed checks are not importable")
    risks = _objects(plan["risks"].get("items"), "risks")
    _ids(risks, "risk")
    if any(item.get("status") != "open" for item in risks):
        raise PlanValidationError("Unexpected risk state")
    return PlanPreview(
        revision=revision, components=len(nodes), connections=len(links),
        milestones=len(milestones), checks=len(checks), risks=len(risks),
        integrations=tuple(item["name"] for item in integrations
                           if isinstance(item.get("name"), str)),
    )
