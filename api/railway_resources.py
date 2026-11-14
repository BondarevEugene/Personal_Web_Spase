"""Link an existing Railway BYOC service to a customer's deployment plan.

The customer selects an existing service from their authorized Railway account.
Every binding is checked live against provider project membership before
being stored. No cloud mutation, secret exposure or billable action.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from automation.deployment import DeploymentSpec, build_plan
from automation.railway_inspection import RailwayInspectError, inspect_binding
from automation.railway_oauth import OAuthConfigurationError, decrypt
from portal.db import session_factory
from portal.models import CloudDeployment, CloudOAuthConnection, CloudRailwayBinding, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/cloud/resources", tags=["Railway Resource Binding"])


class ConnectService(BaseModel):
    plan_id: UUID
    project_id: str = Field(min_length=5, max_length=100)
    environment_id: str = Field(min_length=5, max_length=100)
    service_id: str = Field(min_length=5, max_length=100)


def owner(request: Request, db):
    secure_request(request)
    user = current_customer(request, db)
    if user is None:
        raise HTTPException(401, "Log in to manage Railway resources")
    return user


def csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def plan_for(db, customer_id: str, plan_id: str):
    row = db.scalar(select(CloudDeployment).where(
        CloudDeployment.id == plan_id, CloudDeployment.customer_id == customer_id))
    if row is None:
        raise HTTPException(404, "Cloud plan not found")
    spec = DeploymentSpec.model_validate_json(row.manifest_json)
    if spec.mode != "byoc" or spec.provider != "railway":
        raise HTTPException(409, "Only Railway BYOC plans can be bound to customer services")
    if build_plan(spec).manifest_sha256 != row.manifest_sha256:
        raise HTTPException(409, "Cloud plan integrity mismatch")
    return row


def authorized_connection(db, customer_id: str):
    row = db.scalar(select(CloudOAuthConnection).where(
        CloudOAuthConnection.customer_id == customer_id,
        CloudOAuthConnection.provider == "railway"))
    if not row:
        raise HTTPException(409, "Connect Railway first")
    if row.expires_at <= utcnow():
        raise HTTPException(409, "Railway OAuth token has expired; refresh authorization")
    try:
        return decrypt(row.access_ciphertext)
    except OAuthConfigurationError:
        raise HTTPException(503, "Encrypted connection cannot be read")


def binding_info(row):
    return {
        "id": row.id, "plan_id": row.deployment_id,
        "project_id": row.project_id, "service_id": row.service_id,
        "environment_id": row.environment_id,
        "verified_at": row.verified_at.isoformat() + "Z",
        "last_provider_status": row.last_provider_status,
        "last_checked_at": row.last_checked_at.isoformat() + "Z" if row.last_checked_at else None,
    }


@router.post("/bindings")
def create_binding(request: Request, data: ConnectService):
    with session_factory()() as db:
        user = owner(request, db)
        csrf(request)
        plan = plan_for(db, user.id, str(data.plan_id))
        token = authorized_connection(db, user.id)
        try:
            provider = inspect_binding(token, data.project_id, data.service_id,
                                       data.environment_id)
        except RailwayInspectError as exc:
            raise HTTPException(422, str(exc))
        existing = db.scalar(select(CloudRailwayBinding).where(
            CloudRailwayBinding.deployment_id == plan.id,
            CloudRailwayBinding.customer_id == user.id))
        if existing:
            if (existing.project_id, existing.service_id, existing.environment_id) != (
                data.project_id, data.service_id, data.environment_id
            ):
                raise HTTPException(409, "Disconnect the existing service before linking another")
            row = existing
        else:
            row = CloudRailwayBinding(deployment_id=plan.id, customer_id=user.id,
                                     created_at=utcnow())
            db.add(row)
        row.project_id = data.project_id
        row.service_id = data.service_id
        row.environment_id = data.environment_id
        row.verified_at = utcnow()
        row.last_checked_at = utcnow()
        row.last_provider_status = (provider["deployment"]["status"]
                                    if provider["deployment"] else "NO_DEPLOYMENT")
        row.updated_at = utcnow()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Another request already linked this plan")
        return {"binding": binding_info(row), "provider": provider,
                "note": "Existing Railway service linked; no resources were created"}


@router.get("/bindings/{plan_id}")
def get_binding(plan_id: UUID, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        plan_for(db, user.id, str(plan_id))
        row = db.scalar(select(CloudRailwayBinding).where(
            CloudRailwayBinding.deployment_id == str(plan_id),
            CloudRailwayBinding.customer_id == user.id))
        return {"binding": binding_info(row) if row else None}


@router.get("/bindings/{plan_id}/inspect")
def inspect_saved(plan_id: UUID, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        plan_for(db, user.id, str(plan_id))
        row = db.scalar(select(CloudRailwayBinding).where(
            CloudRailwayBinding.deployment_id == str(plan_id),
            CloudRailwayBinding.customer_id == user.id))
        if not row:
            raise HTTPException(404, "Railway service binding not found")
        token = authorized_connection(db, user.id)
        try:
            data = inspect_binding(token, row.project_id, row.service_id, row.environment_id)
        except RailwayInspectError as exc:
            raise HTTPException(502, str(exc))
        row.last_checked_at = utcnow()
        row.last_provider_status = (data["deployment"]["status"]
                                    if data["deployment"] else "NO_DEPLOYMENT")
        row.updated_at = utcnow()
        db.commit()
        return {"binding": binding_info(row), "provider": data,
                "deployment_is_bot_healthy": False,
                "reason": "A Railway deployment status is not an application healthcheck"}


@router.delete("/bindings/{plan_id}", status_code=204)
def disconnect_binding(plan_id: UUID, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        csrf(request)
        plan_for(db, user.id, str(plan_id))
        row = db.scalar(select(CloudRailwayBinding).where(
            CloudRailwayBinding.deployment_id == str(plan_id),
            CloudRailwayBinding.customer_id == user.id))
        if row:
            db.delete(row)
            db.commit()
    from fastapi import Response
    return Response(status_code=204)
