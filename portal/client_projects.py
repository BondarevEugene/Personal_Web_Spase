"""Client projects: customer requests, milestones, audited operator delivery and acceptance."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from portal.db import session_factory
from portal.project_work import task_context, validate_task_dates
from portal.models import (ClientProject, ClientProjectEvent, ClientProjectMilestone,
                           ClientProjectNotification, ClientProjectTask,
                           ClientProjectTimeEntry, Customer, utcnow)
from portal.project_progress import milestone_progress
from portal.routes import current_customer, form_page
from portal.security import secure_request, verify_csrf
from portal.support_admin import operator_ids, require_operator

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


def notify_org(db, project: ClientProject, message: str):
    """Create bounded per-customer inbox entries, never send email or leak tenants."""
    members = db.scalars(select(Customer).where(
        Customer.org_id == project.org_id, Customer.is_active.is_(True)
    ).limit(100)).all()
    for member in members:
        db.add(ClientProjectNotification(
            recipient_id=member.id, project_id=project.id, message=message[:250],
        ))


def project_context(db, project):
    milestones = db.scalars(select(ClientProjectMilestone).where(
        ClientProjectMilestone.project_id == project.id
    ).order_by(ClientProjectMilestone.ordinal, ClientProjectMilestone.created_at)).all()
    events = db.scalars(select(ClientProjectEvent).where(
        ClientProjectEvent.project_id == project.id
    ).order_by(ClientProjectEvent.created_at, ClientProjectEvent.id).limit(200)).all()
    from portal.project_attachments import attachment_context
    from portal.project_documents import documents_context
    return {"milestones": milestones, "progress": milestone_progress(milestones),
            "events": events, "statuses": STATES,
            "milestone_labels": MILESTONES, **documents_context(db, project),
            **attachment_context(db, project), **task_context(db, project.id)}


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
        notify_org(db, project, "Создан новый заказ: " + project.title)
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
                         project=project, workspace_operator=False,
                         **project_context(db, project))


@router.post("/{id}/request-changes")
def request_project_changes(
    request: Request, id: str, csrf_token: str = Form(""),
    comment: str = Form(""),
):
    """Return delivery to implementation with a traceable client decision.

    Only the customer organization's owner may reject delivery; the existing
    milestones remain available for the operator to reopen or revise.
    """
    secure_request(request)
    verify_csrf(request, csrf_token)
    comment = comment.strip()
    if not 15 <= len(comment) <= 2000:
        raise HTTPException(422, "Укажите замечания: 15–2000 символов")
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        db.refresh(project, with_for_update=True)
        if user.role != "owner":
            raise HTTPException(403, "Доработку может запросить владелец организации")
        if project.status != "review":
            raise HTTPException(409, "Проект не находится на приёмке")
        previous = project.status
        project.status, project.updated_at = "in_progress", utcnow()
        activity(db, project.id, user.id, "revision_requested",
                 "Клиент вернул на доработку: " + comment)
        activity(db, project.id, user.id, "status",
                 previous + " → in_progress")
        notify_org(db, project, "Клиент запросил доработку: " + project.title)
        db.commit()
    return RedirectResponse("/account/projects/" + project.id, status_code=303)


@router.post("/{id}/accept")
def accept_project(request: Request, id: str, csrf_token: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        db.refresh(project, with_for_update=True)
        if user.role != "owner":
            raise HTTPException(403, "Для приёмки требуется владелец организации")
        if project.status != "review":
            raise HTTPException(409, "Проект не передан на приёмку")
        # A specification published during review invalidates any older
        # acknowledgment; acceptance requires the newest document version.
        from portal.models import ClientProjectApproval, ClientProjectDocument
        latest_spec = db.scalar(select(ClientProjectDocument).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == "specification",
        ).order_by(ClientProjectDocument.version.desc()).limit(1))
        if latest_spec is not None:
            approved_latest = db.scalar(select(ClientProjectApproval.id).where(
                ClientProjectApproval.document_id == latest_spec.id,
                ClientProjectApproval.org_id == user.org_id,
            ))
            if approved_latest is None:
                raise HTTPException(409, "Актуальная версия технического задания не согласована")
        # A completed order must have an actual published delivery artifact.
        # Approving milestones alone must not produce an empty handover archive.
        latest_delivery = db.scalar(select(ClientProjectDocument.id).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == "delivery",
        ).order_by(ClientProjectDocument.version.desc()).limit(1))
        if latest_delivery is None:
            raise HTTPException(409, "Опубликуйте описание результата перед приёмкой")
        has_stage = db.scalar(select(ClientProjectMilestone.id).where(
            ClientProjectMilestone.project_id == project.id
        ).limit(1))
        if has_stage is None:
            raise HTTPException(409, "Нет этапов для приёмки")
        incomplete = db.scalar(select(ClientProjectMilestone.id).where(
            ClientProjectMilestone.project_id == project.id,
            ClientProjectMilestone.status != "completed",
        ).limit(1))
        if incomplete is not None:
            raise HTTPException(409, "Не все этапы завершены")
        project.status, project.updated_at = "accepted", utcnow()
        activity(db, project.id, user.id, "acceptance", "Клиент подтвердил приёмку результата")
        notify_org(db, project, "Заказ принят клиентом: " + project.title)
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
                         workspace_operator=True, **project_context(db, project))


@operator_router.post("/{id}/assignment")
def assign_project(request: Request, id: str, csrf_token: str = Form(""),
                   assignee_id: str = Form(""), due_on: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    assignee_id = assignee_id.strip()
    if due_on and len(due_on) != 10:
        raise HTTPException(422, "Дата должна быть YYYY-MM-DD")
    try:
        due_date = datetime.strptime(due_on, "%Y-%m-%d") if due_on else None
    except ValueError:
        raise HTTPException(422, "Некорректная дата")
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        if assignee_id:
            assignee_id = project_key(assignee_id)
            if assignee_id.lower() not in operator_ids():
                raise HTTPException(403, "Назначать можно только операторов платформы")
            customer = db.get(Customer, assignee_id)
            if customer is None or not customer.is_active:
                raise HTTPException(422, "Исполнитель не найден")
        else:
            assignee_id = None
        project.assigned_to_id = assignee_id
        project.due_date = due_date
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "assignment",
                 "Назначен исполнитель " + (assignee_id or "не назначен")
                 + "; дата сдачи " + (due_on or "не назначена"))
        notify_org(db, project, "Обновлён исполнитель или срок заказа: " + project.title)
        db.commit()
    return RedirectResponse("/support/projects/" + project.id, status_code=303)


def require_fresh_delivery_after_revision(db, project_id: str) -> None:
    """Block repeat acceptance until a revised delivery is actually published.

    A client revision request starts a new acceptance cycle. An operator
    must publish a newer delivery document after that request, rather than
    resubmitting the unchanged previous result.
    """
    from portal.models import ClientProjectDocument

    latest_request = db.scalar(select(ClientProjectEvent).where(
        ClientProjectEvent.project_id == project_id,
        ClientProjectEvent.event_type == "revision_requested",
    ).order_by(ClientProjectEvent.created_at.desc(), ClientProjectEvent.id.desc()).limit(1))
    if latest_request is None:
        return
    revised_delivery = db.scalar(select(ClientProjectDocument.id).where(
        ClientProjectDocument.project_id == project_id,
        ClientProjectDocument.document_kind == "delivery",
        ClientProjectDocument.created_at > latest_request.created_at,
    ).limit(1))
    if revised_delivery is None:
        raise HTTPException(
            409,
            "После замечаний клиента опубликуйте новую редакцию результата "
            "перед повторной приёмкой",
        )


@operator_router.post("/{id}/status")
def update_status(request: Request, id: str, csrf_token: str = Form(""),
                  status: str = Form(""), note: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        operator = require_operator(request, db)
        project = operator_project(db, id)
        db.refresh(project, with_for_update=True)
        if status not in NEXT.get(project.status, set()):
            raise HTTPException(409, "Недопустимый переход статуса")
        if len(note.strip()) > 1000:
            raise HTTPException(422, "Комментарий слишком длинный")
        if status == "review":
            from portal.models import ClientProjectDocument
            published_delivery = db.scalar(select(ClientProjectDocument.id).where(
                ClientProjectDocument.project_id == project.id,
                ClientProjectDocument.document_kind == "delivery",
            ).limit(1))
            if published_delivery is None:
                raise HTTPException(409, "Опубликуйте описание результата перед приёмкой")
            require_fresh_delivery_after_revision(db, project.id)
            # A published specification must be acknowledged at its newest
            # revision before delivery can be submitted for acceptance.
            from portal.models import ClientProjectApproval, ClientProjectDocument
            specification = db.scalar(select(ClientProjectDocument).where(
                ClientProjectDocument.project_id == project.id,
                ClientProjectDocument.document_kind == "specification",
            ).order_by(ClientProjectDocument.version.desc()).limit(1))
            if specification is not None:
                approved = db.scalar(select(ClientProjectApproval.id).where(
                    ClientProjectApproval.document_id == specification.id,
                    ClientProjectApproval.org_id == project.org_id,
                ))
                if approved is None:
                    raise HTTPException(409, "Согласуйте последнюю версию технического задания")
            has_stage = db.scalar(select(ClientProjectMilestone.id).where(
                ClientProjectMilestone.project_id == project.id
            ).limit(1))
            if has_stage is None:
                raise HTTPException(409, "Добавьте этапы до приёмки")
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
        notify_org(db, project, "Статус заказа «" + project.title + "»: " + STATES[status])
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


@operator_router.post("/{id}/tasks")
def create_work_task(
    request: Request, id: str, csrf_token: str = Form(""),
    title: str = Form(""), parent_id: str = Form(""),
    assignee_id: str = Form(""), start_on: str = Form(""),
    due_on: str = Form(""), estimate_hours: int = Form(0),
):
    secure_request(request)
    verify_csrf(request, csrf_token)
    title = title.strip()
    if not 3 <= len(title) <= 160 or not 0 <= estimate_hours <= 10000:
        raise HTTPException(422, "Некорректная задача или оценка")
    try:
        start = datetime.strptime(start_on, "%Y-%m-%d") if start_on else None
        due = datetime.strptime(due_on, "%Y-%m-%d") if due_on else None
        validate_task_dates(start, due)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        db.refresh(project, with_for_update=True)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        if db.query(ClientProjectTask).filter_by(project_id=project.id).count() >= 200:
            raise HTTPException(409, "Максимум 200 задач")
        parent = None
        if parent_id:
            parent = db.get(ClientProjectTask, project_key(parent_id))
            if parent is None or parent.project_id != project.id or parent.parent_id:
                raise HTTPException(422, "Родитель должен быть корневой задачей этого проекта")
        assignee = None
        if assignee_id:
            assignee = project_key(assignee_id)
            if assignee.lower() not in operator_ids():
                raise HTTPException(403, "Назначать можно только операторов")
            member = db.get(Customer, assignee)
            if member is None or not member.is_active:
                raise HTTPException(422, "Исполнитель не найден")
        task = ClientProjectTask(project_id=project.id, parent_id=parent.id if parent else None,
                                 title=title, assignee_id=assignee, start_on=start,
                                 due_on=due, estimate_minutes=estimate_hours * 60)
        db.add(task)
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "task", "Добавлена задача: " + title)
        db.commit()
    return RedirectResponse("/support/projects/" + project.id + "#project-work", status_code=303)


@operator_router.post("/{id}/tasks/{task_id}/status")
def change_work_task_status(request: Request, id: str, task_id: str,
                            csrf_token: str = Form(""), status: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    transitions = {"planned": {"in_progress"}, "in_progress": {"planned", "completed"},
                   "completed": {"in_progress"}}
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        db.refresh(project, with_for_update=True)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        task = db.get(ClientProjectTask, project_key(task_id))
        if task is None or task.project_id != project.id:
            raise HTTPException(404, "Задача не найдена")
        if status not in transitions.get(task.status, set()):
            raise HTTPException(409, "Недопустимый переход статуса")
        if status == "completed" and db.scalar(select(ClientProjectTask.id).where(
            ClientProjectTask.parent_id == task.id,
            ClientProjectTask.status != "completed",
        ).limit(1)):
            raise HTTPException(409, "Сначала завершите подзадачи")
        task.status = status
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "task", task.title + ": " + status)
        db.commit()
    return RedirectResponse("/support/projects/" + project.id + "#project-work", status_code=303)


@operator_router.post("/{id}/tasks/{task_id}/time")
def log_work_time(request: Request, id: str, task_id: str,
                  csrf_token: str = Form(""), minutes: int = Form(0),
                  note: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    note = note.strip()
    if not 1 <= minutes <= 1440 or not 3 <= len(note) <= 500:
        raise HTTPException(422, "Укажите 1–1440 минут и описание работы")
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        db.refresh(project, with_for_update=True)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        task = db.get(ClientProjectTask, project_key(task_id))
        if task is None or task.project_id != project.id:
            raise HTTPException(404, "Задача не найдена")
        db.add(ClientProjectTimeEntry(task_id=task.id, actor_id=actor.id,
                                      minutes=minutes, note=note))
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "worklog",
                 f"Учтено {minutes} мин: {task.title}")
        db.commit()
    return RedirectResponse("/support/projects/" + project.id + "#project-work", status_code=303)
