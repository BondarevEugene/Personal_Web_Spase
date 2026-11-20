"""Authenticated saved scenarios for Graph Studio.

All routes are same-origin, session-backed, customer-scoped and CSRF-protected
on mutations. No arbitrary user code, bot tokens or OAuth connections run here.
"""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from api.simple_builder import Scenario, analyze_scenario, export_scenario
from portal.db import session_factory
from portal.models import BuilderProject, utcnow
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


def serialize(project: BuilderProject, full: bool = False) -> dict:
    result = {"id": project.id, "name": project.name,
              "updated_at": project.updated_at.isoformat() + "Z"}
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
