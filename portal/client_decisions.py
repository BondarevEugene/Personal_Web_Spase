"""Customer decision inbox: latest unsigned documents and delivery acceptance."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from portal.client_projects import customer_project
from portal.db import session_factory
from portal.models import ClientProject, ClientProjectApproval, ClientProjectDocument
from portal.routes import current_customer, form_page
from portal.security import secure_request

router = APIRouter(prefix="/account", tags=["Customer decisions"])


@dataclass(frozen=True)
class Decision:
    project: ClientProject
    document: ClientProjectDocument | None
    kind: str


def pending_decisions(db, org_id: str) -> list[Decision]:
    """Return latest outstanding documents plus acceptance tasks for one tenant."""
    projects = db.scalars(
        select(ClientProject)
        .where(
            ClientProject.org_id == org_id,
            ClientProject.status.not_in(("accepted", "cancelled")),
        )
        .order_by(ClientProject.updated_at.desc())
        .limit(100)
    ).all()
    if not projects:
        return []
    project_ids = [p.id for p in projects]
    docs = db.scalars(
        select(ClientProjectDocument)
        .where(ClientProjectDocument.project_id.in_(project_ids))
        .order_by(ClientProjectDocument.version.desc(), ClientProjectDocument.created_at.desc())
    ).all()
    latest = {}
    for doc in docs:
        latest.setdefault((doc.project_id, doc.document_kind), doc)
    approved = set()
    if latest:
        approved = set(db.scalars(
            select(ClientProjectApproval.document_id).where(
                ClientProjectApproval.org_id == org_id,
                ClientProjectApproval.document_id.in_([d.id for d in latest.values()]),
            )
        ).all())
    decisions = []
    for project in projects:
        for (project_id, kind), doc in latest.items():
            if project_id == project.id and doc.id not in approved:
                decisions.append(Decision(project, doc, "document"))
        if project.status == "review":
            decisions.append(Decision(project, None, "acceptance"))
    return decisions


@router.get("/decisions", response_class=HTMLResponse)
def decisions_page(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        decisions = pending_decisions(db, user.org_id)
        return form_page(
            request, "client_decisions.html",
            user=user, decisions=decisions,
        )
