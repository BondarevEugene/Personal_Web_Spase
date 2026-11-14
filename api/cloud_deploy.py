"""Safe first phase of Managed Cloud: planning and customer-owned ledger.

No endpoint in this router creates Railway projects or accepts raw passwords,
API tokens, Telegram bot tokens, or OAuth codes.
"""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from automation.deployment import (
    CloudRunProvider, DeploymentSpec, RailwayProvider, build_plan,
)
from portal.db import session_factory
from portal.models import CloudDeployment, AutomationWorkflow, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/cloud", tags=["OmniFactory Managed Cloud"])


class PlanRequest(BaseModel):
    spec: DeploymentSpec


def require_customer(request: Request, db):
    secure_request(request)
    customer = current_customer(request, db)
    if not customer:
        raise HTTPException(401, "Sign in to manage deployments")
    return customer


def require_csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def parse_uuid(raw: str) -> str:
    try:
        return str(UUID(raw))
    except (ValueError, TypeError):
        raise HTTPException(404, "Deployment plan not found")


def visible(row: CloudDeployment):
    return {
        "id": row.id,
        "name": row.name,
        "mode": row.mode,
        "provider": row.provider,
        "status": row.status,
        "manifest_sha256": row.manifest_sha256,
        "created_at": row.created_at.isoformat() + "Z",
    }


@router.get("/capabilities")
def cloud_capabilities():
    return {
        "product": "OmniFactory Managed Cloud",
        "stage": "planning_foundation",
        "modes": {
            "managed": "Operator-owned Railway; billing and isolation still pending",
            "byoc": "Customer-owned Railway; OAuth authorization pending",
        },
        "providers": {
            "railway": RailwayProvider().readiness(),
            "cloud_run": CloudRunProvider().readiness(),
        },
        "live_deployment_enabled": False,
        "pricing": {"estimate_available": False, "budget_cap_required": True},
        "next_steps": ["Railway OAuth and encrypted token vault",
                       "provider provisioning worker",
                       "runtime image release pipeline",
                       "deployment healthcheck and rollback",
                       "real metering and tenant quotas"],
    }


@router.post("/preview")
def preview_deployment(request: PlanRequest):
    return build_plan(request.spec).model_dump(mode="json")


@router.get("/plans")
def list_deployment_plans(request: Request):
    with session_factory()() as db:
        customer = require_customer(request, db)
        try:
            rows = db.scalars(
                select(CloudDeployment)
                .where(CloudDeployment.customer_id == customer.id)
                .order_by(CloudDeployment.created_at.desc()).limit(50)
            ).all()
            return {"plans": [visible(row) for row in rows]}
        except OperationalError:
            raise HTTPException(503, "Managed Cloud migration is required")


@router.post("/plans", status_code=201)
def save_deployment_plan(
    request: Request, body: PlanRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    with session_factory()() as db:
        customer = require_customer(request, db)
        require_csrf(request)
        if idempotency_key is None or not 8 <= len(idempotency_key) <= 100:
            raise HTTPException(422, "Idempotency-Key (8-100 chars) is required")
        if not all(c.isalnum() or c in "-_:" for c in idempotency_key):
            raise HTTPException(422, "Invalid idempotency key")

        plan = build_plan(body.spec)
        if body.spec.workflow_id:
            owned = db.scalar(select(AutomationWorkflow.id).where(
                AutomationWorkflow.id == body.spec.workflow_id,
                AutomationWorkflow.customer_id == customer.id,
            ))
            if not owned:
                raise HTTPException(404, "Workflow not found in this account")
        try:
            existing = db.scalar(select(CloudDeployment).where(
                CloudDeployment.customer_id == customer.id,
                CloudDeployment.request_key == idempotency_key,
            ))
            if existing:
                if existing.manifest_sha256 != plan.manifest_sha256:
                    raise HTTPException(409, "Idempotency key has a different manifest")
                return visible(existing)
            count = db.scalar(select(func.count()).select_from(CloudDeployment).where(
                CloudDeployment.customer_id == customer.id
            )) or 0
            if count >= 25:
                raise HTTPException(409, "Maximum 25 deployment plans per account")
            row = CloudDeployment(
                customer_id=customer.id,
                name=body.spec.name,
                mode=body.spec.mode,
                provider=body.spec.provider,
                manifest_json=body.spec.model_dump_json(),
                manifest_sha256=plan.manifest_sha256,
                request_key=idempotency_key,
                status="planned",
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return visible(row)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Another request reserved this deployment key")
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Managed Cloud migration is required")


@router.get("/plans/{deployment_id}")
def get_deployment_plan(deployment_id: str, request: Request):
    with session_factory()() as db:
        customer = require_customer(request, db)
        row = db.scalar(select(CloudDeployment).where(
            CloudDeployment.id == parse_uuid(deployment_id),
            CloudDeployment.customer_id == customer.id,
        ))
        if row is None:
            raise HTTPException(404, "Deployment plan not found")
        plan = build_plan(DeploymentSpec.model_validate_json(row.manifest_json))
        if plan.manifest_sha256 != row.manifest_sha256:
            raise HTTPException(409, "Deployment plan integrity mismatch")
        return {"record": visible(row), "plan": plan.model_dump(mode="json")}
