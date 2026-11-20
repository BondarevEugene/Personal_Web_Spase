"""Reproducible customer project handover archive with SHA-256 manifest."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select

from portal.client_projects import customer_project
from portal.db import session_factory
from portal.models import (
    ClientProjectApproval,
    ClientProjectDocument,
    ClientProjectEvent,
    ClientProjectMilestone,
)
from portal.routes import current_customer
from portal.security import secure_request

router = APIRouter(prefix="/account/projects", tags=["Project handover"])
MAX_ARCHIVE_BYTES = 3_000_000


def archive_bytes(project, documents, milestones, events, approvals) -> bytes:
    """Build bounded, stable archive of textual records, not private binary uploads."""
    records = {
        "project.json": {
            "id": project.id,
            "title": project.title,
            "brief": project.brief,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "due_date": project.due_date.isoformat() if project.due_date else None,
        },
        "milestones.json": [
            {"id": row.id, "title": row.title, "details": row.details,
             "status": row.status, "ordinal": row.ordinal}
            for row in milestones
        ],
        "events.json": [
            {"id": row.id, "type": row.event_type, "summary": row.summary,
             "created_at": row.created_at.isoformat()}
            for row in events
        ],
        "approvals.json": [
            {"document_id": row.document_id, "approved_at": row.created_at.isoformat()}
            for row in approvals
        ],
        "documents/index.json": [
            {"id": row.id, "kind": row.document_kind, "title": row.title,
             "version": row.version, "file": f"documents/{row.id}.txt"}
            for row in documents
        ],
    }
    payloads = {
        name: (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        for name, value in records.items()
    }
    for doc in documents:
        payloads[f"documents/{doc.id}.txt"] = doc.body.encode("utf-8")
    payloads["README.txt"] = (
        "OMNIFACTORY — архив проекта\n"
        "Содержит текстовые редакции, этапы, журнал и согласования.\n"
        "Согласования — подтверждения в кабинете, не электронная подпись.\n"
        "Вложения (PDF/изображения) скачиваются отдельно из карточки проекта.\n"
    ).encode()
    if sum(map(len, payloads.values())) > MAX_ARCHIVE_BYTES:
        raise HTTPException(413, "Архив слишком велик; скачайте документы отдельно")
    manifest = {
        "schema": "omnifactory-project-archive-v1",
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payloads.items())},
    }
    payloads["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payloads.items()):
            entry = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o600 << 16
            archive.writestr(entry, data)
    return output.getvalue()


@router.get("/{id}/archive")
def download_project_archive(request: Request, id: str):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        project = customer_project(db, user, id)
        if project.status != "accepted":
            raise HTTPException(409, "Архив передачи доступен после приёмки проекта")
        documents = db.scalars(select(ClientProjectDocument).where(
            ClientProjectDocument.project_id == project.id
        ).order_by(ClientProjectDocument.document_kind, ClientProjectDocument.version)).all()
        milestones = db.scalars(select(ClientProjectMilestone).where(
            ClientProjectMilestone.project_id == project.id
        ).order_by(ClientProjectMilestone.ordinal, ClientProjectMilestone.id)).all()
        events = db.scalars(select(ClientProjectEvent).where(
            ClientProjectEvent.project_id == project.id
        ).order_by(ClientProjectEvent.created_at, ClientProjectEvent.id)).all()
        document_ids = [doc.id for doc in documents]
        approvals = db.scalars(select(ClientProjectApproval).where(
            ClientProjectApproval.org_id == user.org_id,
            ClientProjectApproval.document_id.in_(document_ids),
        ).order_by(ClientProjectApproval.created_at, ClientProjectApproval.id)).all() if document_ids else []
        data = archive_bytes(project, documents, milestones, events, approvals)
    return Response(
        data, media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="omnifactory-project-{project.id}.zip"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Robots-Tag": "noindex, nofollow",
        },
    )
