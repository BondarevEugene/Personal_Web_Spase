"""Owner-scoped operational timeline of saved Telegram bot projects.

This endpoint reports actual database facts. It never treats a dry-run as a
running service and does not perform provider mutations.
"""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from automation.release_gate import scenario_sha256
from portal.db import session_factory
from portal.models import (
    BuilderProject, CloudDeployment, CloudProvisionJob,
    CloudProvisionEvent, CloudReleaseReview,
)
from portal.routes import current_customer
from portal.security import secure_request

router = APIRouter(prefix="/api/v1/builder/operations", tags=["Graph Studio operations"])


@router.get("/{project_id}")
def operations(project_id: UUID, request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Sign in to inspect operations")
        project = db.scalar(select(BuilderProject).where(
            BuilderProject.id == str(project_id),
            BuilderProject.customer_id == user.id,
        ))
        if project is None:
            raise HTTPException(404, "Project not found")
        revision = scenario_sha256(project.scenario_json)
        plans = db.scalars(select(CloudDeployment).where(
            CloudDeployment.customer_id == user.id,
        ).order_by(CloudDeployment.created_at.desc()).limit(50)).all()
        relevant = []
        for plan in plans:
            try:
                spec = json.loads(plan.manifest_json)
            except (ValueError, TypeError):
                continue
            if (spec.get("version") == "graph-" + project.id or
                    str(spec.get("version", "")).startswith(
                        "graph-" + project.id + "-r")):
                relevant.append(plan)
        result = []
        for plan in relevant:
            jobs = db.scalars(select(CloudProvisionJob).where(
                CloudProvisionJob.customer_id == user.id,
                CloudProvisionJob.deployment_id == plan.id,
            ).order_by(CloudProvisionJob.created_at.desc()).limit(20)).all()
            reviews = db.scalars(select(CloudReleaseReview).where(
                CloudReleaseReview.owner_id == user.id,
                CloudReleaseReview.bot_project_id == project.id,
                CloudReleaseReview.cloud_plan_id == plan.id,
            ).order_by(CloudReleaseReview.created_at.desc()).limit(20)).all()
            job_data = []
            for job in jobs:
                events = db.scalars(select(CloudProvisionEvent).where(
                    CloudProvisionEvent.job_id == job.id,
                ).order_by(CloudProvisionEvent.created_at.asc()).limit(100)).all()
                job_data.append({
                    "id": job.id, "mode": job.mode, "status": job.status,
                    "created_at": job.created_at.isoformat() + "Z",
                    "error_code": job.error_code,
                    "events": [{
                        "code": event.code, "message": event.message,
                        "created_at": event.created_at.isoformat() + "Z",
                    } for event in events],
                })
            result.append({
                "id": plan.id, "name": plan.name, "status": plan.status,
                "created_at": plan.created_at.isoformat() + "Z",
                "jobs": job_data,
                "reviews": [{
                    "id": review.id, "status": review.status,
                    "created_at": review.created_at.isoformat() + "Z",
                    "expires_at": review.expires_at.isoformat() + "Z",
                    "revision_matches": review.revision_hash == revision,
                    "cancelled": review.cancelled_at is not None,
                } for review in reviews],
            })
        return {
            "project_id": project.id, "revision_sha256": revision,
            "plans": result, "live_deployment_enabled": False,
            "online_status_verified": False,
            "provider_logs_available": False,
            "limitations": [
                "Dry-run jobs do not create cloud resources",
                "Provider runtime logs and restart controls require live provisioning",
                "Review status is not a deployment status",
            ],
        }
