"""Tenant-owned automation connections and immutable audit events.

Registry only: no OAuth or external token exchange is claimed in this release.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from api.automation import csrf, require_user
from portal.db import session_factory
from portal.models import (AutomationConnection, AutomationConnectionEvent,
                           AutomationCredential, AutomationOAuthState, utcnow)

router = APIRouter(prefix="/api/v1/automation/connections", tags=["Automation Connections"])
PROVIDERS = {
    "google_docs": "Google Docs",
    "google_sheets": "Google Sheets",
    "facebook_page": "Facebook Pages",
    "instagram": "Instagram",
    "http": "HTTPS API",
}


class NewConnection(BaseModel):
    provider: str
    label: str = Field(min_length=2, max_length=100)


def owner(request: Request, db):
    user = require_user(request, db)
    if user.role != "owner":
        raise HTTPException(403, "Owner access required")
    return user


def connection_for(db, customer_id: str, connection_id: str):
    try:
        valid_id = str(UUID(connection_id))
    except (ValueError, TypeError):
        raise HTTPException(404, "Connection not found")
    row = db.scalar(select(AutomationConnection).where(
        AutomationConnection.id == valid_id,
        AutomationConnection.customer_id == customer_id,
    ))
    if row is None:
        raise HTTPException(404, "Connection not found")
    return row


def visible(row):
    return {
        "id": row.id, "provider": row.provider, "label": row.label,
        "status": row.status, "created_at": row.created_at.isoformat() + "Z",
        "authorization": "oauth" if row.provider != "http" else "not_implemented",
        "external_permissions_verified": False,
    }


@router.get("/catalog")
def catalog():
    return {
        "providers": [{"id": key, "name": name,
                       "authorization": "oauth" if key != "http" else "not_implemented"}
                      for key, name in PROVIDERS.items()],
        "notice": "Registration does not authorize an external provider.",
    }


@router.get("")
def list_connections(request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        rows = db.scalars(select(AutomationConnection).where(
            AutomationConnection.customer_id == user.id,
        ).order_by(AutomationConnection.created_at.desc()).limit(100)).all()
        return {"connections": [visible(row) for row in rows]}


@router.post("", status_code=201)
def create_connection(payload: NewConnection, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        csrf(request)
        if payload.provider not in PROVIDERS:
            raise HTTPException(422, "Unsupported provider")
        row = AutomationConnection(
            customer_id=user.id, provider=payload.provider,
            label=payload.label.strip(), status="pending_setup",
        )
        db.add(row)
        try:
            db.flush()
            db.add(AutomationConnectionEvent(
                connection_id=row.id, customer_id=user.id,
                actor_id=user.id, action="registered",
            ))
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Connection label already exists")
        db.refresh(row)
        return visible(row)


@router.get("/{connection_id}")
def get_connection(connection_id: str, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        return visible(connection_for(db, user.id, connection_id))


@router.get("/{connection_id}/audit")
def connection_audit(connection_id: str, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        connection_for(db, user.id, connection_id)
        rows = db.scalars(select(AutomationConnectionEvent).where(
            AutomationConnectionEvent.customer_id == user.id,
            AutomationConnectionEvent.connection_id == connection_id,
        ).order_by(AutomationConnectionEvent.created_at.desc()).limit(100)).all()
        return {"events": [
            {"id": row.id, "action": row.action,
             "created_at": row.created_at.isoformat() + "Z"} for row in rows
        ]}


@router.post("/{connection_id}/disconnect")
def disconnect(connection_id: str, request: Request):
    """Disable registry entry. No remote token exists to revoke yet."""
    with session_factory()() as db:
        user = owner(request, db)
        csrf(request)
        row = connection_for(db, user.id, connection_id)
        if row.status != "disconnected":
            db.execute(delete(AutomationCredential).where(
                AutomationCredential.connection_id == row.id,
                AutomationCredential.customer_id == user.id))
            db.execute(delete(AutomationOAuthState).where(
                AutomationOAuthState.connection_id == row.id,
                AutomationOAuthState.customer_id == user.id))
            row.status = "disconnected"
            row.updated_at = utcnow()
            db.add(AutomationConnectionEvent(
                connection_id=row.id, customer_id=user.id,
                actor_id=user.id, action="disconnected",
            ))
            db.commit()
            db.refresh(row)
        return visible(row)
