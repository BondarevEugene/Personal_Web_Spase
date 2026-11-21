"""Structured, deterministic project plan for an OmniFactory Blueprint.

The plan is advisory only. It contains no credentials, executable code or
customer-submitted prose and cannot trigger external integrations.
"""
from __future__ import annotations

from dataclasses import dataclass

from omni_site.blueprint_specification import Specification


@dataclass(frozen=True)
class ProjectPlan:
    architecture: dict
    milestones: dict
    verification: dict
    risks: dict


def build_project_plan(spec: Specification) -> ProjectPlan:
    brief = spec.blueprint
    revision = spec.revision
    nodes = [
        {"id": f"component-{i:02d}", "label": label, "type": "component"}
        for i, label in enumerate(brief.components, 1)
    ]
    links = [
        {"source": nodes[i]["id"], "target": nodes[i + 1]["id"]}
        for i in range(len(nodes) - 1)
    ]
    architecture = {
        "schema": "omnifactory.blueprint.architecture.v1",
        "revision": revision,
        "status": "proposed",
        "deployable": False,
        "nodes": nodes,
        "links": links,
        "integrations": [
            {"id": option.key, "name": option.title, "connected": False}
            for option in brief.integrations
        ],
    }
    milestones = {
        "schema": "omnifactory.blueprint.milestones.v1",
        "revision": revision,
        "items": [
            {
                "id": f"MS-{i:03d}",
                "title": title,
                "status": "proposed",
                "depends_on": [f"MS-{i - 1:03d}"] if i > 1 else [],
                "deliverable": "Проверяемый результат и протокол приёмки",
            }
            for i, title in enumerate(brief.stages, 1)
        ],
    }
    verification = {
        "schema": "omnifactory.blueprint.verification.v1",
        "revision": revision,
        "status": "not_executed",
        "checks": [
            {
                "id": f"QA-{i:03d}",
                "description": value,
                "result": "not_run",
                "evidence": None,
            }
            for i, value in enumerate(brief.acceptance, 1)
        ],
    }
    risks = {
        "schema": "omnifactory.blueprint.risks.v1",
        "revision": revision,
        "items": [
            {
                "id": f"RISK-{i:03d}",
                "description": value,
                "status": "open",
                "owner": None,
                "mitigation": None,
            }
            for i, value in enumerate(brief.risks, 1)
        ],
    }
    return ProjectPlan(architecture, milestones, verification, risks)
