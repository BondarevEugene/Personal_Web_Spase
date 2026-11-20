"""Two-way, auditable client/operator project communication."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from portal.client_projects import (
    activity,
    customer_project,
    notify_org,
    operator_project,
)
from portal.db import session_factory
from portal.models import ClientProjectEvent, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf
from portal.support_admin import require_operator

customer_router = APIRouter(prefix="/account/projects", tags=["Project conversation"])
operator_router = APIRouter(prefix="/support/projects", tags=["Project conversation"])
MAX_MESSAGES = 500


def validate_message(body: str) -> str:
    body = body.strip()
    if not 10 <= len(body) <= 2000:
        raise HTTPException(422, "Сообщение: от 10 до 2000 символов")
    return body


def add_message(db, project, actor, body: str, sender: str) -> None:
    """Write message and notification in the same transaction."""
    if project.status in {"accepted", "cancelled"}:
        raise HTTPException(409, "Обсуждение закрытого проекта недоступно")
    count = db.scalar(select(func.count(ClientProjectEvent.id)).where(
        ClientProjectEvent.project_id == project.id,
        ClientProjectEvent.event_type == "project_message",
    )) or 0
    if count >= MAX_MESSAGES:
        raise HTTPException(409, "Лимит переписки достигнут; используйте поддержку")
    activity(db, project.id, actor.id, "project_message", f"{sender}: {body}")
    project.updated_at = utcnow()
    notify_org(db, project, f"Новое сообщение по проекту «{project.title}» ({sender})")


@customer_router.post("/{id}/messages")
def customer_message(
    request: Request, id: str,
    csrf_token: str = Form(""), body: str = Form(""),
):
    secure_request(request)
    verify_csrf(request, csrf_token)
    body = validate_message(body)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        db.refresh(project, with_for_update=True)
        add_message(db, project, user, body, "Клиент")
        db.commit()
    return RedirectResponse("/account/projects/" + project.id + "#project-dialogue", status_code=303)


@operator_router.post("/{id}/messages")
def operator_message(
    request: Request, id: str,
    csrf_token: str = Form(""), body: str = Form(""),
):
    secure_request(request)
    verify_csrf(request, csrf_token)
    body = validate_message(body)
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        db.refresh(project, with_for_update=True)
        add_message(db, project, actor, body, "Оператор")
        db.commit()
    return RedirectResponse("/support/projects/" + project.id + "#project-dialogue", status_code=303)
