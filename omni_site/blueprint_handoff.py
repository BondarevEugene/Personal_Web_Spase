"""Explicit Blueprint -> customer project handoff using existing portal schema.

Creates a REQUEST, never a paid order or a confirmed implementation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from omni_site.blueprint_export import BlueprintInput
from omni_site.blueprint_specification import compile_specification
from portal.client_projects import activity, notify_org
from portal.db import session_factory
from portal.models import (
    ClientProject,
    ClientProjectDocument,
    utcnow,
)
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(tags=["Blueprint client handoff"])


class HandoffInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blueprint: BlueprintInput
    title: str = Field(min_length=5, max_length=160)


@router.post("/api/v1/blueprint/handoff", status_code=201)
def create_blueprint_handoff(request: Request, payload: HandoffInput):
    """Save the specification as immutable v1 of a new organization request."""
    secure_request(request)
    try:
        spec = compile_specification(
            sector=payload.blueprint.sector,
            team=payload.blueprint.team,
            process=payload.blueprint.process,
            priority=payload.blueprint.priority,
            integrations=tuple(payload.blueprint.integrations),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Войдите в кабинет для передачи проекта")
        verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
        try:
            count = db.scalar(
                select(func.count(ClientProject.id)).where(
                    ClientProject.org_id == user.org_id,
                    ClientProject.status == "requested",
                )
            ) or 0
            if count >= 25:
                raise HTTPException(409, "Слишком много открытых заявок")
            title = payload.title.strip()
            if len(title) < 5:
                raise HTTPException(422, "Название должно содержать 5 символов")
            now = utcnow()
            project = ClientProject(
                org_id=user.org_id,
                created_by_id=user.id,
                title=title,
                brief=(
                    f"Blueprint Studio / {spec.blueprint.title}\n"
                    f"Редакция: {spec.revision}\n"
                    "Предварительная заявка, не договор и не подтверждённая оплата."
                ),
                status="requested",
                created_at=now,
                updated_at=now,
            )
            db.add(project)
            db.flush()
            db.add(ClientProjectDocument(
                project_id=project.id,
                created_by_id=user.id,
                document_kind="specification",
                version=1,
                title=f"Предварительное ТЗ · {spec.revision}",
                body=spec.markdown,
            ))
            activity(
                db, project.id, user.id, "request",
                f"Blueprint Studio: заявка и ТЗ v1, редакция {spec.revision}",
            )
            notify_org(db, project, "Новая заявка Blueprint: " + title)
            db.commit()
        except OperationalError as exc:
            db.rollback()
            raise HTTPException(
                503, "База портала недоступна или не применены миграции"
            ) from exc
    return {
        "id": project.id,
        "revision": spec.revision,
        "status": "requested",
        "url": f"/account/projects/{project.id}",
    }
