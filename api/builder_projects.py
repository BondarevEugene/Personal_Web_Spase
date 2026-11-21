"""Authenticated saved scenarios for Graph Studio.

All routes are same-origin, session-backed, customer-scoped and CSRF-protected
on mutations. No arbitrary user code, bot tokens or OAuth connections run here.
"""
from __future__ import annotations

import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from api.simple_builder import (
    Scenario,
    SimulationRequest,
    analyze_scenario,
    export_scenario,
    release_preflight,
    simulate_scenario,
)
from automation.deployment import DeploymentSpec, build_plan
from api.graph_release_evidence import release_evidence
from portal.db import session_factory
from portal.models import BuilderProject, CloudDeployment, utcnow
from portal.routes import current_customer
from portal.security import issue_csrf, secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/builder/projects", tags=["Graph Studio projects"])


class Coordinates(BaseModel):
    x: float = Field(ge=0, le=2200, allow_inf_nan=False)
    y: float = Field(ge=0, le=8000, allow_inf_nan=False)


class CanvasGroup(BaseModel):
    """Organizational annotation, not an executable node or subgraph."""

    id: str = Field(pattern=r"^group[0-9]{1,6}$")
    title: str = Field(min_length=2, max_length=60)
    node_ids: list[str] = Field(min_length=1, max_length=80)


class ProjectData(BaseModel):
    scenario: Scenario
    positions: dict[str, Coordinates] = Field(default_factory=dict, max_length=80)
    groups: list[CanvasGroup] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def checked_groups(self):
        nodes = {node.id for node in self.scenario.nodes}
        ids = [group.id for group in self.groups]
        members = [node_id for group in self.groups for node_id in group.node_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("Повторяющиеся идентификаторы групп")
        if len(members) != len(set(members)) or not set(members).issubset(nodes):
            raise ValueError("Группы должны содержать существующие узлы без повторов")
        return self

    def checked_positions(self) -> dict:
        ids = {node.id for node in self.scenario.nodes}
        if not set(self.positions).issubset(ids):
            raise HTTPException(422, "Layout references unknown node")
        return {node: point.model_dump() for node, point in self.positions.items()}


def pack_layout(data: ProjectData) -> str:
    """Keep old positions-only rows readable while saving new annotations."""
    return json.dumps({
        "positions": data.checked_positions(),
        "groups": [group.model_dump() for group in data.groups],
    })


def unpack_layout(raw: str) -> tuple[dict, list]:
    content = json.loads(raw or "{}")
    if not isinstance(content, dict):
        return {}, []
    if "positions" in content and isinstance(content["positions"], dict):
        groups = content.get("groups", [])
        return content["positions"], groups if isinstance(groups, list) else []
    return content, []


def customer_required(request: Request, db):
    secure_request(request)
    customer = current_customer(request, db)
    if customer is None:
        raise HTTPException(401, detail="Sign in at /account/login to manage projects")
    return customer


def project_revision(project: BuilderProject) -> str:
    """Digest of the saved graph and layout."""
    payload = (project.scenario_json + chr(0) + project.layout_json).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ensure_revision(request: Request, project: BuilderProject) -> None:
    """Prevent stale editors overwriting newer work when If-Match is supplied."""
    expected = request.headers.get("If-Match")
    if expected is not None and expected != project_revision(project):
        raise HTTPException(409, detail={
            "code": "PROJECT_CHANGED",
            "message": "Проект изменился в другой вкладке. Обновите страницу.",
            "current_revision": project_revision(project),
        })


def serialize(project: BuilderProject, full: bool = False) -> dict:
    result = {"id": project.id, "name": project.name,
              "updated_at": project.updated_at.isoformat() + "Z",
              "revision": project_revision(project)}
    if full:
        result["scenario"] = json.loads(project.scenario_json)
        result["positions"], result["groups"] = unpack_layout(project.layout_json)
    return result


def project_id(raw: str) -> str:
    try:
        return str(UUID(raw))
    except (ValueError, AttributeError):
        raise HTTPException(404, detail="Project not found")


@router.get("/csrf")
def csrf_token(request: Request, response: Response):
    with session_factory()() as db:
        customer_required(request, db)
    return {"csrf_token": issue_csrf(response, request)}


@router.get("")
def list_projects(request: Request):
    with session_factory()() as db:
        user = customer_required(request, db)
        try:
            rows = db.scalars(
                select(BuilderProject).where(BuilderProject.customer_id == user.id)
                .order_by(BuilderProject.updated_at.desc()).limit(50)
            ).all()
        except OperationalError:
            raise HTTPException(503, "Apply portal Alembic migrations before saving")
        return {"projects": [serialize(row) for row in rows]}


@router.post("", status_code=201)
def create_project(request: Request, data: ProjectData):
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        layout = pack_layout(data)
        try:
            count = db.scalar(
                select(func.count()).select_from(BuilderProject)
                .where(BuilderProject.customer_id == user.id)
            ) or 0
            if count >= 50:
                raise HTTPException(409, "Maximum 50 saved projects per account")
            now = utcnow()
            row = BuilderProject(
                customer_id=user.id, name=data.scenario.name,
                scenario_json=data.scenario.model_dump_json(),
                layout_json=layout,
                created_at=now, updated_at=now,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply portal Alembic migrations before saving")
        return serialize(row)


@router.get("/{id}")
def get_project(id: str, request: Request):
    with session_factory()() as db:
        user = customer_required(request, db)
        try:
            row = db.scalar(select(BuilderProject).where(
                BuilderProject.id == project_id(id),
                BuilderProject.customer_id == user.id,
            ))
        except OperationalError:
            raise HTTPException(503, "Apply portal Alembic migrations before saving")
        if row is None:
            raise HTTPException(404, detail="Project not found")
        return serialize(row, full=True)


@router.put("/{id}")
def update_project(id: str, request: Request, data: ProjectData):
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        layout = pack_layout(data)
        try:
            row = db.scalar(select(BuilderProject).where(
                BuilderProject.id == project_id(id),
                BuilderProject.customer_id == user.id,
            ))
            if row is None:
                raise HTTPException(404, detail="Project not found")
            ensure_revision(request, row)
            row.name = data.scenario.name
            row.scenario_json = data.scenario.model_dump_json()
            row.layout_json = layout
            row.updated_at = utcnow()
            db.commit()
            return serialize(row)
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply portal Alembic migrations before saving")


@router.delete("/{id}", status_code=204)
def delete_project(id: str, request: Request):
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        try:
            row = db.scalar(select(BuilderProject).where(
                BuilderProject.id == project_id(id),
                BuilderProject.customer_id == user.id,
            ))
            if row is None:
                raise HTTPException(404, detail="Project not found")
            ensure_revision(request, row)
            db.delete(row)
            db.commit()
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply portal Alembic migrations before saving")
    return Response(status_code=204)


@router.get("/{id}/diagnostics")
def project_diagnostics(id: str, request: Request):
    """Validate the persisted version, not unsaved browser state."""
    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
    return analyze_scenario(scenario)


def workflow_report(scenario: Scenario, project: BuilderProject) -> dict:
    """Single truthful workflow snapshot for the persisted project revision."""
    preflight = release_preflight(scenario)
    simulation = simulate_scenario(SimulationRequest(scenario=scenario))
    return {
        "project_id": project.id,
        "revision": project_revision(project),
        "stages": [
            {"id": "created", "status": "complete"},
            {"id": "saved", "status": "complete"},
            {"id": "validated", "status": "complete" if preflight["ready"] else "blocked"},
            {"id": "simulated", "status": simulation["status"]},
            {"id": "export", "status": "ready" if preflight["ready"] else "blocked"},
            {"id": "deployment", "status": "manual"},
        ],
        "preflight": preflight,
        "simulation": simulation,
        "export_available": preflight["ready"],
        "export_url": f"/api/v1/builder/projects/{project.id}/export"
        if preflight["ready"] else None,
        "live_deployment_enabled": False,
        "instructions": (
            "Сценарий готов к экспорту. Для запуска нужен BOT_TOKEN "
            "и настроенный Python-хостинг."
            if preflight["ready"]
            else "Исправьте ошибки preflight и сохраните новую ревизию."
        ),
    }


@router.get("/{id}/workflow")
def project_workflow(id: str, request: Request):
    """One customer-scoped read-only endpoint for the whole builder journey."""
    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
        return workflow_report(scenario, row)


@router.get("/{id}/export")
def export_saved_project(id: str, request: Request):
    """Export a customer's saved graph without accepting arbitrary graph payloads."""
    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
    return export_scenario(scenario)


@router.post("/{id}/duplicate", status_code=201)
def duplicate_project(id: str, request: Request):
    """Create an independent revision candidate with its own ID and layout."""
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        source = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if source is None:
            raise HTTPException(404, "Project not found")
        count = db.scalar(select(func.count()).select_from(BuilderProject).where(
            BuilderProject.customer_id == user.id,
        )) or 0
        if count >= 50:
            raise HTTPException(409, "Maximum 50 saved projects per account")
        scenario = Scenario.model_validate_json(source.scenario_json)
        scenario.name = (scenario.name[:92] + " · копия")[:100]
        now = utcnow()
        copy = BuilderProject(
            customer_id=user.id,
            name=scenario.name,
            scenario_json=scenario.model_dump_json(),
            layout_json=source.layout_json,
            created_at=now,
            updated_at=now,
        )
        db.add(copy)
        db.commit()
        db.refresh(copy)
        return serialize(copy)


class GraphDeploymentRequest(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    mode: str = Field(default="managed")
    transport: str = Field(default="worker")
    max_monthly_usd: int = Field(ge=5, le=10000)


@router.get("/{id}/deployment-readiness")
def graph_deployment_readiness(id: str, request: Request):
    """Report truthful deployment readiness for an owned saved graph."""
    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
        report = analyze_scenario(scenario)
        plans = db.scalars(select(CloudDeployment).where(
            CloudDeployment.customer_id == user.id,
        ).order_by(CloudDeployment.created_at.desc()).limit(50)).all()
        linked = []
        for plan in plans:
            try:
                manifest = json.loads(plan.manifest_json)
            except (ValueError, TypeError):
                continue
            if manifest.get("version") == "graph-" + row.id:
                linked.append({
                    "id": plan.id, "name": plan.name, "status": plan.status,
                    "manifest_sha256": plan.manifest_sha256,
                })
        return {
            "project_id": row.id, "scenario_valid": report["ok"],
            "diagnostics": report, "saved_plans": linked,
            "live_deployment_enabled": False,
            "token_collection_enabled": False,
            "next_step": "Экспортировать aiogram ZIP или сохранить dry-run план",
        }


@router.post("/{id}/deployment-plan", status_code=201)
def create_graph_deployment_plan(
    id: str, request: Request, body: GraphDeploymentRequest,
):
    """Create an auditable plan, never provision or collect credentials."""
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
        report = analyze_scenario(scenario)
        if not report["ok"]:
            raise HTTPException(422, detail={
                "message": "Исправьте ошибки сценария перед планированием",
                "issues": report["issues"],
            })
        spec = DeploymentSpec(
            name=body.name, runtime="telegram_aiogram",
            mode=body.mode, provider="railway",
            transport=body.transport, version="graph-" + row.id,
            max_monthly_usd=body.max_monthly_usd,
            secret_refs=["BOT_TOKEN"],
        )
        plan = build_plan(spec)
        existing = db.scalar(select(CloudDeployment).where(
            CloudDeployment.customer_id == user.id,
            CloudDeployment.manifest_sha256 == plan.manifest_sha256,
        ))
        if existing is not None:
            return {"id": existing.id, "status": existing.status,
                    "manifest_sha256": existing.manifest_sha256,
                    "already_exists": True}
        count = db.scalar(select(func.count()).select_from(CloudDeployment).where(
            CloudDeployment.customer_id == user.id,
        )) or 0
        if count >= 25:
            raise HTTPException(409, "Maximum 25 deployment plans per account")
        now = utcnow()
        new = CloudDeployment(
            customer_id=user.id, name=spec.name, mode=spec.mode,
            provider=spec.provider, manifest_json=spec.model_dump_json(),
            manifest_sha256=plan.manifest_sha256,
            request_key="graph-" + plan.manifest_sha256[:32],
            status="planned", created_at=now, updated_at=now,
        )
        db.add(new)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "План создан параллельным запросом. Обновите страницу.")
        db.refresh(new)
        return {"id": new.id, "status": new.status,
                "manifest_sha256": new.manifest_sha256,
                "already_exists": False, "warnings": plan.warnings}



@router.get("/{id}/backup")
def download_project_backup(id: str, request: Request):
    """Export a self-contained editable graph, never credentials."""
    from fastapi.responses import JSONResponse

    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        data = serialize(row, full=True)
        return JSONResponse({
            "format": "omnifactory.graph-project.backup",
            "version": 1,
            "revision": data["revision"],
            "project": {
                "scenario": data["scenario"],
                "positions": data["positions"],
                "groups": data["groups"],
            },
        }, headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="omnifactory-graph-backup.json"',
            "X-Content-Type-Options": "nosniff",
        })


class RestoreRequest(BaseModel):
    format: str
    version: int
    project: ProjectData


@router.post("/{id}/restore")
def restore_project_backup(id: str, request: Request, body: RestoreRequest):
    """Restore an owned backup with an explicit revision precondition."""
    if body.format != "omnifactory.graph-project.backup" or body.version != 1:
        raise HTTPException(422, "Unsupported backup format or version")
    with session_factory()() as db:
        user = customer_required(request, db)
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        if not request.headers.get("If-Match"):
            raise HTTPException(428, "If-Match revision required for restore")
        ensure_revision(request, row)
        row.name = body.project.scenario.name
        row.scenario_json = body.project.scenario.model_dump_json()
        row.layout_json = pack_layout(body.project)
        row.updated_at = utcnow()
        db.commit()
        return serialize(row, full=True)


@router.get("/{id}/release-evidence")
def saved_graph_release_evidence(id: str, request: Request):
    """Evidence is scoped to the logged-in owner and exact persisted revision."""
    with session_factory()() as db:
        user = customer_required(request, db)
        row = db.scalar(select(BuilderProject).where(
            BuilderProject.id == project_id(id),
            BuilderProject.customer_id == user.id,
        ))
        if row is None:
            raise HTTPException(404, "Project not found")
        scenario = Scenario.model_validate_json(row.scenario_json)
        return release_evidence(scenario, row.id, project_revision(row))
