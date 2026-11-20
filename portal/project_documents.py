"""Project text-document revisions and explicit acknowledgments.

A project document is UTF-8 text stored in the DB; no uploads, e-signatures,
external notifications or AI interpretation is asserted by these endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from portal.client_projects import activity, customer_project, notify_org, operator_project, project_key
from portal.db import session_factory
from portal.models import (ClientProjectApproval, ClientProjectDocument,
                           ClientProjectNotification, utcnow)
from portal.routes import current_customer, form_page
from portal.security import secure_request, verify_csrf
from portal.support_admin import require_operator

customer_router = APIRouter(prefix="/account/projects", tags=["Project Documents"])
operator_router = APIRouter(prefix="/support/projects", tags=["Operator Documents"])
inbox_router = APIRouter(prefix="/account/notifications", tags=["Customer Inbox"])
KINDS = {"specification": "Техническое задание",
         "delivery": "Описание результата", "other": "Документ проекта"}


def documents_context(db, project):
    docs = db.scalars(select(ClientProjectDocument).where(
        ClientProjectDocument.project_id == project.id
    ).order_by(ClientProjectDocument.created_at.desc(), ClientProjectDocument.version.desc())
                      .limit(100)).all()
    latest = {}
    for doc in docs:
        current = latest.get(doc.document_kind)
        if current is None or doc.version > current.version:
            latest[doc.document_kind] = doc
    approvals = db.scalars(select(ClientProjectApproval).where(
        ClientProjectApproval.document_id.in_([d.id for d in docs])
    )).all() if docs else []
    return {"project_documents": docs, "document_kinds": KINDS,
            "latest_documents": latest, "approved_documents": {
                a.document_id for a in approvals}}


@operator_router.post("/{id}/documents")
def publish_document(request: Request, id: str, csrf_token: str = Form(""),
                     kind: str = Form(""), title: str = Form(""),
                     body: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    title, body = title.strip(), body.strip()
    if kind not in KINDS or not 4 <= len(title) <= 160 or not 30 <= len(body) <= 12000:
        raise HTTPException(422, "Документ: тип, название 4–160, текст 30–12000 символов")
    with session_factory()() as db:
        actor = require_operator(request, db)
        project = operator_project(db, id)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Закрытый проект нельзя редактировать")
        previous = db.scalar(select(func.max(ClientProjectDocument.version)).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == kind,
        )) or 0
        document = ClientProjectDocument(
            project_id=project.id, created_by_id=actor.id, document_kind=kind,
            title=title, body=body, version=previous + 1,
        )
        db.add(document)
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "document",
                 "Опубликован документ «" + title + "», версия " + str(document.version))
        notify_org(db, project, "Новая версия документа: " + title)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Одновременная публикация: обновите страницу")
    return RedirectResponse("/support/projects/" + project.id, status_code=303)


@customer_router.post("/{id}/documents/{document_id}/approve")
def approve_document(request: Request, id: str, document_id: str,
                     csrf_token: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    from portal.client_projects import project_key

    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        if user.role != "owner":
            raise HTTPException(403, "Согласует только владелец организации")
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        doc = db.scalar(select(ClientProjectDocument).where(
            ClientProjectDocument.id == project_key(document_id),
            ClientProjectDocument.project_id == project.id,
        ))
        if doc is None:
            raise HTTPException(404, "Документ не найден")
        latest = db.scalar(select(func.max(ClientProjectDocument.version)).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == doc.document_kind,
        ))
        if doc.version != latest:
            raise HTTPException(409, "Согласовать можно только последнюю версию")
        existing = db.scalar(select(ClientProjectApproval.id).where(
            ClientProjectApproval.document_id == doc.id,
            ClientProjectApproval.org_id == user.org_id,
        ))
        if existing is not None:
            return RedirectResponse("/account/projects/" + project.id, status_code=303)
        db.add(ClientProjectApproval(
            document_id=doc.id, org_id=user.org_id, approved_by_id=user.id,
        ))
        project.updated_at = utcnow()
        activity(db, project.id, user.id, "document_approval",
                 "Согласован документ «" + doc.title + "», версия " + str(doc.version))
        db.commit()
    return RedirectResponse("/account/projects/" + project.id, status_code=303)



@customer_router.post("/{id}/documents/{document_id}/request-revision")
def request_document_revision(
    request: Request, id: str, document_id: str,
    csrf_token: str = Form(""), comment: str = Form(""),
):
    """Request changes to the latest specification without approving it."""
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
            raise HTTPException(403, "Изменения запрашивает владелец организации")
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Проект закрыт")
        doc = db.scalar(select(ClientProjectDocument).where(
            ClientProjectDocument.id == project_key(document_id),
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == "specification",
        ))
        if doc is None:
            raise HTTPException(404, "Техническое задание не найдено")
        latest = db.scalar(select(func.max(ClientProjectDocument.version)).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == "specification",
        ))
        if doc.version != latest:
            raise HTTPException(409, "Запросить изменения можно только к актуальной версии")
        approved = db.scalar(select(ClientProjectApproval.id).where(
            ClientProjectApproval.document_id == doc.id,
            ClientProjectApproval.org_id == user.org_id,
        ))
        if approved is not None:
            raise HTTPException(409, "Версия уже согласована; запросите новую редакцию через поддержку")
        if project.status == "review":
            project.status = "in_progress"
        project.updated_at = utcnow()
        activity(db, project.id, user.id, "specification_revision_requested",
                 f"Замечания к ТЗ v{doc.version}: {comment}")
        notify_org(db, project, f"Клиент запросил изменения ТЗ v{doc.version}: {project.title}")
        db.commit()
    return RedirectResponse("/account/projects/" + project.id, status_code=303)


@inbox_router.get("", response_class=HTMLResponse)
def notifications(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        rows = db.scalars(select(ClientProjectNotification).where(
            ClientProjectNotification.recipient_id == user.id
        ).order_by(ClientProjectNotification.created_at.desc()).limit(100)).all()
        return form_page(request, "client_notifications.html", user=user, notices=rows)


@inbox_router.post("/{id}/read")
def mark_notification_read(request: Request, id: str,
                           csrf_token: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    from portal.client_projects import project_key

    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        notice = db.scalar(select(ClientProjectNotification).where(
            ClientProjectNotification.id == project_key(id),
            ClientProjectNotification.recipient_id == user.id,
        ))
        if notice is None:
            raise HTTPException(404, "Уведомление не найдено")
        if notice.read_at is None:
            notice.read_at = utcnow()
            db.commit()
    return RedirectResponse("/account/notifications", status_code=303)
