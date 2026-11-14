"""Authenticated Bot Lab inventory and Railway resource discovery.

No fabricated runtime metrics, no provider mutations. Owned customer data only.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from automation.railway_inventory import RailwayReadError, list_projects
from automation.railway_oauth import OAuthConfigurationError, decrypt
from portal.db import session_factory
from portal.models import (AutomationWorkflow, BuilderProject,
                           CloudDeployment, CloudOAuthConnection, utcnow)
from portal.routes import current_customer
from portal.security import secure_request

router = APIRouter(prefix="/api/v1/bot-lab", tags=["OmniFactory Bot Lab"])


def require_customer(request: Request, db):
    secure_request(request)
    customer = current_customer(request, db)
    if not customer:
        raise HTTPException(401, "Sign in to use Bot Lab")
    return customer


@router.get("/overview")
def overview(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        try:
            bots = db.scalars(select(BuilderProject).where(
                BuilderProject.customer_id == user.id
            ).order_by(BuilderProject.updated_at.desc()).limit(50)).all()
            workflows = db.scalars(select(AutomationWorkflow).where(
                AutomationWorkflow.customer_id == user.id
            ).order_by(AutomationWorkflow.updated_at.desc()).limit(50)).all()
            plans = db.scalars(select(CloudDeployment).where(
                CloudDeployment.customer_id == user.id
            ).order_by(CloudDeployment.updated_at.desc()).limit(50)).all()
            connection = db.scalar(select(CloudOAuthConnection).where(
                CloudOAuthConnection.customer_id == user.id,
                CloudOAuthConnection.provider == "railway"))
        except OperationalError:
            raise HTTPException(503, "Apply Bot Lab/Cloud database migrations")
        return {
            "bot_projects": [
                {"id": p.id, "name": p.name, "updated_at": p.updated_at.isoformat() + "Z",
                 "status": "draft", "editor": "/architect"}
                for p in bots
            ],
            "automations": [
                {"id": w.id, "name": w.name, "revision": w.revision,
                 "updated_at": w.updated_at.isoformat() + "Z", "editor": "/automation/studio"}
                for w in workflows
            ],
            "deployments": [
                {"id": p.id, "name": p.name, "mode": p.mode,
                 "provider": p.provider, "status": p.status,
                 "created_at": p.created_at.isoformat() + "Z",
                 "updated_at": p.updated_at.isoformat() + "Z"}
                for p in plans
            ],
            "railway": {
                "connected": bool(connection),
                "account_name": connection.remote_name if connection else None,
                "access_expires_at": connection.expires_at.isoformat() + "Z" if connection else None,
                "refresh_available": bool(connection and connection.refresh_ciphertext),
            },
            "capabilities": {
                "real_deployment": False,
                "external_projects": "read_only",
                "logs": "not_connected",
                "restart": "not_available",
                "rollback": "not_available",
                "costs": "not_connected",
            },
        }


@router.get("/railway/projects")
def railway_projects(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        try:
            connection = db.scalar(select(CloudOAuthConnection).where(
                CloudOAuthConnection.customer_id == user.id,
                CloudOAuthConnection.provider == "railway"))
        except OperationalError:
            raise HTTPException(503, "Apply Railway OAuth migration")
        if not connection:
            raise HTTPException(409, "Connect Railway before requesting projects")
        if connection.expires_at <= utcnow():
            raise HTTPException(409, "Railway access expired. Refresh it from Cloud Deploy.")
        try:
            projects = list_projects(decrypt(connection.access_ciphertext))
        except OAuthConfigurationError:
            raise HTTPException(503, "Railway token vault unavailable")
        except RailwayReadError as exc:
            raise HTTPException(502, str(exc))
        return {"projects": projects, "source": "railway_graphql",
                "checked_at": utcnow().isoformat() + "Z",
                "note": "Read-only. Project access depends on customer-approved OAuth permissions."}
