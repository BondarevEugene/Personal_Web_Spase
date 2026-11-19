"""Small, private project attachments with bounded upload size and strict ownership.

Not a general-purpose blob store. The database holds up to eight files, each
at most 2 MiB, per project. All downloads are forced attachments.
"""
from __future__ import annotations

import hashlib
import re

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from portal.client_projects import activity, customer_project, notify_org, operator_project, project_key
from portal.db import session_factory
from portal.models import ClientProjectAttachment, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf
from portal.support_admin import require_operator

customer_router = APIRouter(prefix="/account/projects", tags=["Project Attachments"])
operator_router = APIRouter(prefix="/support/projects", tags=["Operator Attachments"])

MAX_FILE = 2 * 1024 * 1024
MAX_FILES = 8
MAX_TOTAL = 8 * 1024 * 1024
ALLOWED = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain",
}


def safe_name(raw: str) -> str:
    """Store a display-only basename, never a client filesystem path."""
    name = str(raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip().strip(".")
    if not name or len(name) > 120 or "/" in name:
        raise HTTPException(422, "Недопустимое имя файла (максимум 120 символов)")
    return name


def checked_data(filename: str, data: bytes) -> str:
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime = ALLOWED.get(suffix)
    if mime is None or not 1 <= len(data) <= MAX_FILE:
        raise HTTPException(422, "Доступны PDF, PNG, JPEG и TXT размером до 2 МБ")
    valid = (
        data.startswith(b"%PDF-") and b"%%EOF" in data[-1024:]
        if mime == "application/pdf" else
        data.startswith(b"\x89PNG\r\n\x1a\n") if mime == "image/png" else
        data.startswith(b"\xff\xd8\xff") if mime == "image/jpeg" else
        is_utf8_text(data)
    )
    if not valid:
        raise HTTPException(422, "Содержимое файла не соответствует расширению")
    return mime


def is_utf8_text(content: bytes) -> bool:
    try:
        decoded = content.decode("utf-8")
        return "\x00" not in decoded
    except UnicodeDecodeError:
        return False


def attachment_context(db, project):
    records = db.scalars(select(ClientProjectAttachment).where(
        ClientProjectAttachment.project_id == project.id
    ).order_by(ClientProjectAttachment.created_at.desc(),
               ClientProjectAttachment.id.desc()).limit(MAX_FILES)).all()
    return {"project_attachments": records,
            "attachment_limit_mb": MAX_FILE // (1024 * 1024)}


async def upload(request: Request, id: str, csrf_token: str, uploaded: UploadFile,
                 *, as_operator: bool):
    secure_request(request)
    verify_csrf(request, csrf_token)
    filename = safe_name(uploaded.filename or "")
    # Read max + 1 bytes, never stream an unbounded user body into memory.
    try:
        data = await uploaded.read(MAX_FILE + 1)
    finally:
        await uploaded.close()
    mime = checked_data(filename, data)
    with session_factory()() as db:
        if as_operator:
            actor = require_operator(request, db)
            project = operator_project(db, id)
        else:
            actor = current_customer(request, db)
            if actor is None:
                return RedirectResponse("/account/login", status_code=303)
            project = customer_project(db, actor, id)
        if project.status in {"accepted", "cancelled"}:
            raise HTTPException(409, "Закрытый проект нельзя изменять")
        count, used = db.execute(select(
            func.count(ClientProjectAttachment.id),
            func.coalesce(func.sum(ClientProjectAttachment.size_bytes), 0),
        ).where(ClientProjectAttachment.project_id == project.id)).one()
        if count >= MAX_FILES or used + len(data) > MAX_TOTAL:
            raise HTTPException(413, "Лимит файлов проекта: 8 вложений / 8 МБ")
        previous = db.scalar(select(func.max(ClientProjectAttachment.version)).where(
            ClientProjectAttachment.project_id == project.id,
            ClientProjectAttachment.filename == filename,
        )) or 0
        attachment = ClientProjectAttachment(
            project_id=project.id, uploaded_by_id=actor.id,
            filename=filename, version=previous + 1,
            mime_type=mime, size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(), data=data,
        )
        db.add(attachment)
        project.updated_at = utcnow()
        activity(db, project.id, actor.id, "attachment",
                 "Загружен файл: " + filename)
        notify_org(db, project, "Добавлен файл к заказу: " + filename)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "Версия файла уже создана; обновите страницу") from exc
    destination = "/support/projects/" if as_operator else "/account/projects/"
    return RedirectResponse(destination + project.id, status_code=303)


@customer_router.post("/{id}/attachments")
async def upload_customer_file(request: Request, id: str,
                               csrf_token: str = Form(""),
                               uploaded: UploadFile = File(...)):
    return await upload(request, id, csrf_token, uploaded, as_operator=False)


@operator_router.post("/{id}/attachments")
async def upload_operator_file(request: Request, id: str,
                               csrf_token: str = Form(""),
                               uploaded: UploadFile = File(...)):
    return await upload(request, id, csrf_token, uploaded, as_operator=True)


def download(request: Request, id: str, attachment_id: str, *, as_operator: bool):
    secure_request(request)
    with session_factory()() as db:
        if as_operator:
            require_operator(request, db)
            project = operator_project(db, id)
        else:
            actor = current_customer(request, db)
            if actor is None:
                return RedirectResponse("/account/login", status_code=303)
            project = customer_project(db, actor, id)
        row = db.scalar(select(ClientProjectAttachment).where(
            ClientProjectAttachment.id == project_key(attachment_id),
            ClientProjectAttachment.project_id == project.id,
        ))
        if row is None:
            raise HTTPException(404, "Файл не найден")
        extension = "." + row.filename.rsplit(".", 1)[-1].lower()
        return Response(content=row.data, media_type="application/octet-stream",
                        headers={
                            "Content-Disposition":
                                f'attachment; filename="project-{row.id}{extension}"',
                            "Content-Security-Policy": "sandbox",
                            "X-Content-Type-Options": "nosniff",
                            "Cache-Control": "private, no-store",
                        })


@customer_router.get("/{id}/attachments/{attachment_id}")
def download_customer_file(request: Request, id: str, attachment_id: str):
    return download(request, id, attachment_id, as_operator=False)


@operator_router.get("/{id}/attachments/{attachment_id}")
def download_operator_file(request: Request, id: str, attachment_id: str):
    return download(request, id, attachment_id, as_operator=True)
