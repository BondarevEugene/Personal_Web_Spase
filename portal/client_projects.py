"""Client projects: customer requests, milestones, audited operator delivery and acceptance."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from portal.db import session_factory
from portal.models import ClientProject, ClientProjectEvent, ClientProjectMilestone, utcnow
from portal.routes import current_customer, form_page
from portal.security import secure_request, verify_csrf
from portal.support_admin import require_operator

router = APIRouter(prefix="/account/projects", tags=["Customer Projects"])
operator_router = APIRouter(prefix="/support/projects", tags=["Project Operations"])
STATES = {
    "requested": "Новый запрос", "planning": "Планирование",
    "in_progress": "В разработке", "review": "Ожидает приёмки",
    "accepted": "Принят клиентом", "paused": "Приостановлен",
    "cancelled": "Отменён",
}
NEXT = {
    "requested": {"planning", "cancelled"},
    "planning": {"in_progress", "paused", "cancelled"},
    "in_progress": {"review", "paused", "cancelled"},
    "paused": {"planning", "in_progress", "cancelled"},
    "review": {"in_progress", "paused"},
    "accepted": set(), "cancelled": set(),
}
MILESTONES = {"planned": "Запланирован", "in_progress": "В работе", "completed": "Завершён"}


def project_key(value: str) -> str:
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(404, "Project not found")


def customer_project(db, user, raw: str) -> ClientProject:
    project = db.scalar(select(ClientProject).where(
        ClientProject.id == project_key(raw),
        ClientProject.org_id == user.org_id,
    ))
    if project is None:
        raise HTTPException(404, "Project not found")
    return project


def operator_project(db, raw: str) -> ClientProject:
    project = db.get(ClientProject, project_key(raw))
    if project is None:
        raise HTTPException(404, "Project not found")
    return project


def activity(db, project_id: str, actor_id: str, kind: str, summary: str):
    db.add(ClientProjectEvent(project_id=project_id, actor_id=actor_id,
                              event_type=kind, summary=summary))


def project_context(db, project):
    milestones = db.scalars(select(ClientProjectMilestone).where(
        ClientProjectMilestone.project_id == project.id
    ).order_by(ClientProjectMilestone.ordinal, ClientProjectMilestone.created_at)).all()
    events = db.scalars(select(ClientProjectEvent).where(
        ClientProjectEvent.project_id == project.id
    ).order_by(ClientProjectEvent.created_at, ClientProjectEvent.id).limit(200)).all()
    return {"milestones": milestones, "events": events, "statuses": STATES,
            "milestone_labels": MILESTONES}


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def projects_page(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        projects = db.scalars(select(ClientProject).where(
            ClientProject.org_id == user.org_id
        ).order_by(ClientProject.updated_at.desc()).limit(100)).all()
        return form_page(request, "client_projects.html", user=user, projects=projects,
                         statuses=STATES, created=request.query_params.get("created") == "1")


@router.post("")
def create_project(request: Request, csrf_token: str = Form(""),
                   title: str = Form(""), brief: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    title, brief = title.strip(), brief.strip()
    if not 5 <= len(title) <= 160 or not 20 <= len(brief) <= 5000:
        raise HTTPException(422, "Тема: 5–160; описание: 20–5000 символов")
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        project = ClientProject(org_id=user.org_id, created_by_id=user.id,
                                title=title, brief=brief, status="requested")
        db.add(project)
        db.flush()
        activity(db, project.id, user.id, "request", "Клиент отправил запрос на проект")
        db.commit()
    return RedirectResponse("/account/projects?created=1", status_code=303)


@router.get("/{id}", response_class=HTMLResponse)
def project_detail(request: Request, id: str):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        return form_page(request, "client_project_detail.html", user=user,
                         project=project, **project_context(db, project))


@router.post("/{id}/accept")
def accept_project(request: Request, id: str, csrf_token: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        if user.role != "owner":
            raise HTTPException(403, "Для приёмки требуется владелец организации")
        if project.status != "review":
            raise HTTPException(409, "Проект не передан на приёмку")
        incomplete = db.scalar(select(ClientProjectMilestone.id).where(
            ClientProjectMilestone.project_id == project.id,
            ClientProjectMilestone.status != "completed",
        ).limit(1))
        if incomplete is not None:
            raise HTTPException(409, "Не все этапы завершены")
        project.status, project.updated_at = "accepted", utcnow()
        activity(db, project.id, user.id, "acceptance", "Клиент подтвердил приёмку результата")
        db.commit()
    return RedirectResponse("/account/projects/" + project.id, status_code=303)


@operator_router.get("", response_class=HTMLResponse)
def operator_queue(request: Request):
    with session_factory()() as db:
        operator = require_operator(request, db)
        rows = db.scalars(select(ClientProject).order_by(
            ClientProject.updated_at.desc()).limit(150)).all()
        return form_page(request, "client_project_operator.html",
                         user=operator, projects=rows, project=None,
                         statuses=STATES, milestone_labels=MILESTONES)


@operator_router.get("/{id}", response_class=HTMLResponse)
def operator_detail(request: Request, id: str):
    with session_factory()() as db:
        operator = require_operator(request, db)
        project = operator_project(db, id)
        rows = db.scalars(select(ClientProject).order_by(
            ClientProject.updated_at.desc()).limit(150)).all()
        return form_page(request, "client_project_operator.html",
                         user=operator, projects=rows, project=project,
                         **project_context(db, project))


@operator_router.post("/{id}/status")
def update_status(request: Request, id: str, csrf_token: str = Form(""),
                  status: str = Form(""), note: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        operator = require_operator(request, db)
        project = operator_project(db, id)
        if status not in NEXT.get(project.status, set()):
            raise HTTPException(409, "Недопустимый переход статуса")
        if len(note.strip()) > 1000:
            raise HTTPException(422, "Комментарий слишком длинный")
        if status == "review":
            incomplete = db.scalar(select(ClientProjectMilestone.id).where(
                ClientProjectMilestone.project_id == project.id,
                ClientProjectMilestone.status != "completed",
            ).limit(1))
            if incomplete is not None:
                raise HTTPException(409, "Завершите этапы перед приёмкой")
        previous = project.status
        project.status, project.updated_at = status, utcnow()
        activity(db, project.id, operator.id, "status",
                 previous + " → " + status + (": " + note.strip() if note.strip() else ""))
        db.commit()
    return RedirectResponse("/support/projects/" + project.id, status_code=303)


@operator_router.post("/{id}/milestones")
def add_milestone(request: Request, id: str, csrf_token: str = Form(""),
                  title: str = Form(""), details: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    if not 3 <= len(title.strip()) <= 160 or len(details) > 2000:
        raise HTTPException(422, "Некорректное название или описание этапа")
    with session_factory()() as db:
        operator = require_operator(request, db)
        project = operator_project(db, id)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        existing = db.scalars(select(ClientProjectMilestone).where(
            ClientProjectMilestone.project_id == project.id
        )).all()
        if len(existing) >= 40:
            raise HTTPException(409, "Максимум 40 этапов")
        stage = ClientProjectMilestone(project_id=project.id, title=title.strip(),
                                       details=details.strip(), status="planned",
                                       ordinal=len(existing) + 1)
        db.add(stage)
        project.updated_at = utcnow()
        activity(db, project.id, operator.id, "milestone",
                 "Создан этап: " + stage.title)
        db.commit()
    return RedirectResponse("/support/projects/" + project.id, status_code=303)


@operator_router.post("/{id}/milestones/{stage_id}")
def update_milestone(request: Request, id: str, stage_id: str,
                     csrf_token: str = Form(""), status: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        operator = require_operator(request, db)
        project = operator_project(db, id)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        stage = db.scalar(select(ClientProjectMilestone).where(
            ClientProjectMilestone.id == project_key(stage_id),
            ClientProjectMilestone.project_id == project.id,
        ))
        if stage is None:
            raise HTTPException(404, "Этап не найден")
        changes = {"planned": {"in_progress"},
                   "in_progress": {"completed", "planned"},
                   "completed": {"in_progress"}}
        if status not in changes.get(stage.status, set()):
            raise HTTPException(409, "Недопустимый переход этапа")
        old = stage.status
        stage.status, stage.updated_at = status, utcnow()
        project.updated_at = utcnow()
        activity(db, project.id, operator.id, "milestone",
                 stage.title + ": " + old + " → " + status)
        db.commit()
    return RedirectResponse("/support/projects/" + project.id, status_code=303)
