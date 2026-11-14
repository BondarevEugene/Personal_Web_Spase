"""Customer-scoped deployment job queue (dry-run only in this release).

Job creation does not approve a charge or create Railway resources. All jobs
pin the complete original manifest and idempotency key, are auditable and can
be cancelled before a worker claims them.
"""
from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from automation.deployment import DeploymentSpec, build_plan
from portal.db import session_factory
from portal.models import CloudDeployment, CloudProvisionEvent, CloudProvisionJob, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/cloud/provision", tags=["Managed Cloud Provisioning"])


class EnqueueRequest(BaseModel):
    plan_id: UUID
    confirmation: str = Field(min_length=12, max_length=100)


def logged_in(request: Request, db):
    secure_request(request)
    customer = current_customer(request, db)
    if customer is None:
        raise HTTPException(401, "Sign in to manage deployment jobs")
    return customer


def require_csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def details(row: CloudProvisionJob) -> dict:
    return {
        "id": row.id, "plan_id": row.deployment_id, "status": row.status,
        "mode": row.mode, "created_at": row.created_at.isoformat() + "Z",
        "updated_at": row.updated_at.isoformat() + "Z",
        "manifest_sha256": row.manifest_sha256,
        "provider_project_id": row.provider_project_id,
        "provider_service_id": row.provider_service_id,
        "provider_deployment_id": row.provider_deployment_id,
        "error_code": row.error_code,
        "billable_actions_permitted": False,
    }


def owned_job(db, customer_id: str, job_id: str) -> CloudProvisionJob:
    try:
        uid = str(UUID(job_id))
    except ValueError:
        raise HTTPException(404, "Provision job not found")
    row = db.scalar(select(CloudProvisionJob).where(
        CloudProvisionJob.id == uid,
        CloudProvisionJob.customer_id == customer_id,
    ))
    if row is None:
        raise HTTPException(404, "Provision job not found")
    return row


@router.get("/capabilities")
def capabilities():
    return {
        "stage": "dry_run_worker",
        "queue": "durable", "immutable_manifest": True,
        "worker": "separate_process", "railway_mutations_enabled": False,
        "provider_quote_verified": False,
        "supported_job_modes": ["dry_run"],
        "requires_real_deploy_for_online_status": True,
    }


@router.get("/jobs")
def list_jobs(request: Request):
    with session_factory()() as db:
        user = logged_in(request, db)
        try:
            rows = db.scalars(select(CloudProvisionJob).where(
                CloudProvisionJob.customer_id == user.id,
            ).order_by(CloudProvisionJob.created_at.desc()).limit(50)).all()
        except OperationalError:
            raise HTTPException(503, "Apply provisioning migration")
        return {"jobs": [details(row) for row in rows]}


@router.post("/jobs", status_code=201)
def enqueue(request: Request, body: EnqueueRequest,
            idempotency_key: str | None = Header(None, alias="Idempotency-Key")):
    with session_factory()() as db:
        user = logged_in(request, db)
        require_csrf(request)
        if not idempotency_key or not re.fullmatch(r"[A-Za-z0-9_:-]{8,100}", idempotency_key):
            raise HTTPException(422, "Idempotency-Key of 8–100 safe characters required")
        if body.confirmation != "SIMULATE DEPLOYMENT":
            raise HTTPException(422, "Confirmation must be SIMULATE DEPLOYMENT")
        try:
            plan = db.scalar(select(CloudDeployment).where(
                CloudDeployment.id == str(body.plan_id),
                CloudDeployment.customer_id == user.id,
            ))
            if plan is None:
                raise HTTPException(404, "Deployment plan not found")
            spec = DeploymentSpec.model_validate_json(plan.manifest_json)
            manifest = build_plan(spec)
            if manifest.manifest_sha256 != plan.manifest_sha256:
                raise HTTPException(409, "Deployment plan integrity mismatch")
            existing = db.scalar(select(CloudProvisionJob).where(
                CloudProvisionJob.customer_id == user.id,
                CloudProvisionJob.request_key == idempotency_key,
            ))
            if existing:
                if existing.deployment_id != plan.id or existing.manifest_sha256 != plan.manifest_sha256:
                    raise HTTPException(409, "Idempotency key belongs to different deployment")
                return details(existing)
            if plan.status != "planned":
                raise HTTPException(409, "Deployment plan is not in planned state")
            now = utcnow()
            row = CloudProvisionJob(
                customer_id=user.id,
                deployment_id=plan.id,
                request_key=idempotency_key,
                manifest_sha256=plan.manifest_sha256,
                manifest_snapshot=plan.manifest_json,
                status="queued", mode="dry_run", created_at=now, updated_at=now,
            )
            db.add(row)
            db.flush()
            db.add(CloudProvisionEvent(
                job_id=row.id, code="queued",
                message="Dry-run job accepted; no paid Railway resources will be created",
                created_at=now))
            db.commit()
            db.refresh(row)
            return details(row)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Concurrent duplicate job; refresh list")
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply provisioning migration")


@router.get("/jobs/{job_id}")
def get_job(job_id: str, request: Request):
    with session_factory()() as db:
        user = logged_in(request, db)
        row = owned_job(db, user.id, job_id)
        events = db.scalars(select(CloudProvisionEvent).where(
            CloudProvisionEvent.job_id == row.id,
        ).order_by(CloudProvisionEvent.created_at.asc()).limit(100)).all()
        return {
            **details(row),
            "events": [{"code": e.code, "message": e.message,
                        "created_at": e.created_at.isoformat() + "Z"} for e in events],
        }


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, request: Request):
    with session_factory()() as db:
        user = logged_in(request, db)
        require_csrf(request)
        row = owned_job(db, user.id, job_id)
        if row.status != "queued":
            raise HTTPException(409, "Only jobs waiting in queue may be cancelled")
        row.status = "cancelled"
        row.updated_at = utcnow()
        db.add(CloudProvisionEvent(job_id=row.id, code="cancelled",
                                   message="Queued dry-run cancelled by customer",
                                   created_at=utcnow()))
        db.commit()
        return details(row)
