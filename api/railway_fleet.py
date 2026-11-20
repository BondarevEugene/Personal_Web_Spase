"""Read-only Railway fleet inspection for the authenticated account.

Never performs provider mutations, claims Telegram delivery, or exposes OAuth
tokens. Provider failures are isolated per service.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from automation.railway_inspection import RailwayInspectError, inspect_binding
from automation.railway_reconciliation import classify, summarize
from automation.railway_oauth import OAuthConfigurationError, decrypt
from portal.db import session_factory
from portal.models import CloudDeployment, CloudOAuthConnection, CloudRailwayBinding, utcnow
from portal.routes import current_customer
from portal.security import secure_request

router = APIRouter(prefix="/api/v1/cloud/fleet", tags=["Railway Fleet Observability"])


@router.get("/capabilities")
def capabilities():
    return {
        "read_only": True,
        "provider_deployment_status": True,
        "telegram_delivery_verified": False,
        "remote_restart_enabled": False,
        "remote_stop_enabled": False,
        "remote_rollback_enabled": False,
        "live_provisioning_enabled": False,
        "fleet_reconciliation": True,
        "status_freshness_minutes": 15,
    }


@router.get("/services")
def services(request: Request, refresh: bool = False):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Sign in to inspect Railway services")
        bindings = db.scalars(select(CloudRailwayBinding).where(
            CloudRailwayBinding.customer_id == user.id,
        ).order_by(CloudRailwayBinding.created_at.desc()).limit(50)).all()
        plans = {
            p.id: p for p in db.scalars(select(CloudDeployment).where(
                CloudDeployment.customer_id == user.id,
            )).all()
        }
        token = None
        if refresh and bindings:
            conn = db.scalar(select(CloudOAuthConnection).where(
                CloudOAuthConnection.customer_id == user.id,
                CloudOAuthConnection.provider == "railway",
            ))
            if conn is None or conn.expires_at <= utcnow():
                raise HTTPException(409, "Reconnect Railway to refresh live status")
            try:
                token = decrypt(conn.access_ciphertext)
            except OAuthConfigurationError:
                raise HTTPException(503, "Railway OAuth configuration unavailable")
        rows = []
        now = utcnow()
        for binding in bindings:
            plan = plans.get(binding.deployment_id)
            if plan is None:
                continue
            entry = {
                "binding_id": binding.id, "plan_id": plan.id,
                "plan_name": plan.name, "plan_status": plan.status,
                "project_id": binding.project_id,
                "service_id": binding.service_id,
                "environment_id": binding.environment_id,
                "last_checked_at": (
                    binding.last_checked_at.isoformat() + "Z"
                    if binding.last_checked_at else None),
                "provider_status": binding.last_provider_status,
                "provider_live": False,
                "provider_error": None,
                "telegram_delivery_verified": False,
                "runtime_healthy": None,
            }
            if refresh:
                try:
                    provider = inspect_binding(
                        token, binding.project_id, binding.service_id,
                        binding.environment_id)
                    deployment = provider.get("deployment")
                    entry["provider_status"] = (
                        deployment["status"] if deployment else "NO_DEPLOYMENT")
                    entry["provider_live"] = True
                    entry["replicas"] = provider["instance"]["replicas"]
                    entry["healthcheck_configured"] = provider["instance"][
                        "healthcheck_configured"]
                    binding.last_checked_at = utcnow()
                    entry["last_checked_at"] = binding.last_checked_at.isoformat() + "Z"
                    binding.last_provider_status = entry["provider_status"]
                    binding.updated_at = utcnow()
                except RailwayInspectError:
                    entry["provider_error"] = "Provider inspection unavailable"
            status = classify(
                provider_status=entry["provider_status"],
                last_checked_at=binding.last_checked_at if not entry["provider_live"]
                else now,
                now=now,
                inspection_failed=bool(entry["provider_error"]),
            )
            entry["reconciliation"] = status
            rows.append(entry)
        if refresh:
            db.commit()
        return {
            "services": rows,
            "summary": summarize([row["reconciliation"] for row in rows]),
            "source": "railway_live" if refresh else "database_cache",
            "online_status_verified": False,
            "provider_mutations_enabled": False,
        }
