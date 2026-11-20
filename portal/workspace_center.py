"""Organization-scoped project command center using existing operational records."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import case, func, select

from portal.client_projects import STATES
from portal.db import session_factory
from portal.models import (
    ClientProject,
    ClientProjectApproval,
    ClientProjectDocument,
    ClientProjectMilestone,
    ClientProjectNotification,
)
from portal.routes import current_customer, form_page
from portal.security import secure_request

router = APIRouter(prefix="/account", tags=["Customer command center"])
OPEN_STATES = ("requested", "planning", "in_progress", "review", "paused")
FILTERS = {"all", "active", "review", "completed"}


@dataclass(frozen=True)
class ProjectPulse:
    project: ClientProject
    total: int
    completed: int
    percent: int
    spec_version: int | None
    spec_approved: bool
    requires_action: bool


def project_pulses(db, projects: list[ClientProject], org_id: str) -> list[ProjectPulse]:
    """Batch-query milestones, latest specifications and approvals (no N+1)."""
    if not projects:
        return []
    ids = [p.id for p in projects]
    stages = db.execute(
        select(
            ClientProjectMilestone.project_id,
            func.count(ClientProjectMilestone.id),
            func.sum(case((ClientProjectMilestone.status == "completed", 1), else_=0)),
        )
        .where(ClientProjectMilestone.project_id.in_(ids))
        .group_by(ClientProjectMilestone.project_id)
    ).all()
    stage_counts = {pid: (total, done or 0) for pid, total, done in stages}
    docs = db.scalars(
        select(ClientProjectDocument)
        .where(
            ClientProjectDocument.project_id.in_(ids),
            ClientProjectDocument.document_kind == "specification",
        )
        .order_by(ClientProjectDocument.version.desc())
    ).all()
    latest = {}
    for doc in docs:
        latest.setdefault(doc.project_id, doc)
    approved_ids = set()
    if latest:
        approved_ids = set(db.scalars(
            select(ClientProjectApproval.document_id).where(
                ClientProjectApproval.document_id.in_([d.id for d in latest.values()]),
                ClientProjectApproval.org_id == org_id,
            )
        ).all())
    pulses = []
    for project in projects:
        total, completed = stage_counts.get(project.id, (0, 0))
        spec = latest.get(project.id)
        approved = spec is not None and spec.id in approved_ids
        needs_action = project.status == "review" or (
            spec is not None and not approved and project.status in OPEN_STATES
        )
        pulses.append(ProjectPulse(
            project=project,
            total=total,
            completed=completed,
            percent=round(completed * 100 / total) if total else 0,
            spec_version=spec.version if spec else None,
            spec_approved=approved,
            requires_action=needs_action,
        ))
    return pulses


@router.get("/workspace", response_class=HTMLResponse)
def workspace(request: Request, status: str = "all"):
    secure_request(request)
    if status not in FILTERS:
        status = "all"
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        projects = db.scalars(
            select(ClientProject)
            .where(ClientProject.org_id == user.org_id)
            .order_by(ClientProject.updated_at.desc(), ClientProject.id.desc())
            .limit(100)
        ).all()
        pulses = project_pulses(db, projects, user.org_id)
        metrics = {
            "total": len(pulses),
            "active": sum(p.project.status in OPEN_STATES for p in pulses),
            "review": sum(p.project.status == "review" for p in pulses),
            "attention": sum(p.requires_action for p in pulses),
            "completed": sum(p.project.status == "accepted" for p in pulses),
        }
        if status == "active":
            pulses = [p for p in pulses if p.project.status in OPEN_STATES]
        elif status == "review":
            pulses = [p for p in pulses if p.requires_action]
        elif status == "completed":
            pulses = [p for p in pulses if p.project.status == "accepted"]
        unread = db.scalar(select(func.count(ClientProjectNotification.id)).where(
            ClientProjectNotification.recipient_id == user.id,
            ClientProjectNotification.read_at.is_(None),
        )) or 0
        return form_page(
            request, "client_workspace_center.html", user=user,
            pulses=pulses, metrics=metrics, unread=unread,
            current_filter=status, statuses=STATES,
        )
