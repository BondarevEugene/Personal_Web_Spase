"""OmniFactory Automation API: authenticated definitions, dry-runs and audits.

Public webhooks are opt-in, per-workflow token-protected and dry-run-only.
Live connector execution must be manually requested by an authenticated owner
and explicitly enabled by the operator. No background task is silently started.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from automation.engine import RunRequest, WorkflowDefinition, bounded, execute
from automation.connector_diagnostics import diagnose, operator_overview
from automation.diagnostics import analyze
from omni_site.automation_flagship import BY_SLUG, template_definition
from portal.db import session_factory
from portal.models import AutomationRun, AutomationWorkflow, AutomationSchedule, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/automation", tags=["Automation Engine"])
WEBHOOKS = APIRouter(prefix="/hooks/automation", tags=["Automation Webhooks"])


class ScheduleRequest(BaseModel):
    interval_minutes: int = Field(ge=5, le=10080)
    enabled: bool = True


class SaveWorkflow(BaseModel):
    definition: WorkflowDefinition
    revision: int | None = Field(default=None, ge=1)


def require_user(request: Request, db):
    secure_request(request)
    user = current_customer(request, db)
    if not user:
        raise HTTPException(401, "Sign in at /account/login")
    return user


def csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def parse_id(raw: str) -> str:
    try:
        return str(UUID(raw))
    except (ValueError, TypeError):
        raise HTTPException(404, "Workflow not found")


def row_for(db, user_id: str, workflow_id: str) -> AutomationWorkflow:
    row = db.scalar(select(AutomationWorkflow).where(
        AutomationWorkflow.id == parse_id(workflow_id),
        AutomationWorkflow.customer_id == user_id))
    if row is None:
        raise HTTPException(404, "Workflow not found")
    return row


def visible(row: AutomationWorkflow, *, full=False):
    result = {"id": row.id, "name": row.name, "revision": row.revision,
              "updated_at": row.updated_at.isoformat() + "Z",
              "webhook_enabled": bool(row.webhook_token_hash)}
    if full:
        result["definition"] = json.loads(row.definition_json)
    return result


def run_visible(row: AutomationRun):
    return {"id": row.id, "workflow_id": row.workflow_id,
            "revision": row.workflow_revision, "status": row.status,
            "mode": row.mode, "trace": json.loads(row.trace_json),
            "created_at": row.created_at.isoformat() + "Z"}


def record_run(db, workflow: AutomationWorkflow, *, input_data: dict,
               live: bool, idempotency_key: str | None):
    """Reserve an execution row BEFORE side effects.

    A duplicate request cannot concurrently publish a second post. A crashed
    live run remains in 'running' state and requires operator reconciliation,
    not an automatic retry.
    """
    bounded(input_data)
    row = AutomationRun(
        workflow_id=workflow.id, customer_id=workflow.customer_id,
        workflow_revision=workflow.revision, status="running",
        mode="live" if live else "dry_run",
        idempotency_key=idempotency_key, trace_json="[]",
        created_at=utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        result = execute(WorkflowDefinition.model_validate_json(workflow.definition_json),
                         input_data, live=live)
        row.status = result.status
        row.trace_json = json.dumps(result.trace, ensure_ascii=False)
        db.commit()
    except Exception:
        db.rollback()
        row.status = "failed"
        row.trace_json = json.dumps([{"outcome": "failed", "error": "Execution aborted"}])
        db.add(row)
        db.commit()
        raise
    return run_visible(row)

@router.get("/connectors/readiness")
def connector_readiness(request: Request):
    """Read-only, owner-scoped prerequisites; never return credential values."""
    with session_factory()() as db:
        user = require_user(request, db)
        if user.role != "owner":
            raise HTTPException(403, "Owner access required")
    enabled = os.getenv("OMNI_AUTOMATION_LIVE_ENABLED") == "1"
    configured = {
        "google_docs": bool(os.getenv("OMNI_CREDENTIAL_GOOGLE")),
        "google_sheets": bool(os.getenv("OMNI_CREDENTIAL_GOOGLE")),
        "facebook_page": bool(os.getenv("OMNI_CREDENTIAL_FACEBOOK")),
        "instagram": bool(os.getenv("OMNI_CREDENTIAL_INSTAGRAM")),
        "http": bool(os.getenv("OMNI_AUTOMATION_ALLOWED_HOSTS"))
        and bool(os.getenv("OMNI_AUTOMATION_EGRESS_PROXY"))
        and os.getenv("OMNI_AUTOMATION_HTTP_LIVE_ENABLED") == "1",
    }
    return {
        "live_enabled": enabled,
        "connectors": [
            {"kind": kind, "configured": ready,
             "live_available": bool(enabled and ready)}
            for kind, ready in configured.items()
        ],
        "configuration_mode": "operator_environment_only",
        "credentials_exposed": False,
        "notice": "Configured does not prove external API permissions or connectivity.",
    }


@router.get("/connectors/diagnostics")
def connector_diagnostics(request: Request):
    """Owner-only connector operator-gate preflight; no provider calls."""
    with session_factory()() as db:
        user = require_user(request, db)
        if user.role != "owner":
            raise HTTPException(403, "Owner access required")
    return operator_overview()


@router.get("/workflows/{workflow_id}/connectors/diagnostics")
def workflow_connector_diagnostics(workflow_id: str, request: Request):
    """Owner-only, tenant-scoped workflow connector configuration preflight."""
    with session_factory()() as db:
        user = require_user(request, db)
        if user.role != "owner":
            raise HTTPException(403, "Owner access required")
        workflow = row_for(db, user.id, workflow_id)
        definition = WorkflowDefinition.model_validate_json(workflow.definition_json)
        result = diagnose(definition)
        return {"workflow_id": workflow.id, "revision": workflow.revision, **result}


@router.get("/catalog")
def catalog():
    return {"version": "v1", "supported": [
        "trigger", "set", "condition", "transform", "http", "google_docs",
        "google_sheets", "facebook_page", "instagram", "approval", "end"],
        "default_mode": "dry_run",
        "scheduler": "interval 5–10080 minutes; requires separate worker process",
        "external_calls_require": ["OMNI_AUTOMATION_LIVE_ENABLED=1",
                                   "per-connector operator secrets",
                                   "authenticated owner confirmation"],
        "capabilities": {"webhook_trigger": "signed_token_dry_run",
                         "google_docs": "create_document",
                         "google_sheets": "append_rows",
                         "facebook_page": "publish_post",
                         "instagram": "publish_image",
                         "http": "operator_allowlisted_https"},
        "not_available": ["hosted Telegram deployment", "interactive OAuth",
                          "always-on scheduler hosting", "arbitrary Python execution"]}


@router.post("/analyze")
def review_workflow(definition: WorkflowDefinition):
    """Static quality analysis without running or publishing anything."""
    return analyze(definition)


@router.get("/templates")
def available_templates():
    """Safe, server-maintained templates; no user credentials or dynamic code."""
    return {"templates": [
        {"slug": item.slug, "title": item.title, "audience": item.audience,
         "description": item.description}
        for item in BY_SLUG.values()
    ]}


@router.post("/templates/{slug}/install", status_code=201)
def install_template(slug: str, request: Request):
    """Clone a server-owned template into the authenticated customer's workspace."""
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        if slug not in BY_SLUG:
            raise HTTPException(404, "Template not found")
        definition = template_definition(slug)
        try:
            count = db.scalar(
                select(func.count()).select_from(AutomationWorkflow)
                .where(AutomationWorkflow.customer_id == user.id)
            )
            if count >= 50:
                raise HTTPException(409, "Maximum 50 workflows per account")
            row = AutomationWorkflow(
                customer_id=user.id, name=definition.name,
                definition_json=definition.model_dump_json(),
                revision=1, created_at=utcnow(), updated_at=utcnow(),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return visible(row, full=True)
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply automation Alembic migration")


@router.get("/workflows")
def workflows(request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        try:
            rows = db.scalars(
                select(AutomationWorkflow)
                .where(AutomationWorkflow.customer_id == user.id)
                .order_by(AutomationWorkflow.updated_at.desc()).limit(50)
            ).all()
            return {"workflows": [visible(w) for w in rows]}
        except OperationalError:
            raise HTTPException(503, "Apply automation Alembic migration")


@router.post("/workflows", status_code=201)
def create_workflow(request: Request, data: SaveWorkflow):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        try:
            count = db.scalar(select(func.count()).select_from(AutomationWorkflow)
                              .where(AutomationWorkflow.customer_id == user.id))
            if count >= 50:
                raise HTTPException(409, "Maximum 50 workflows per account")
            row = AutomationWorkflow(
                customer_id=user.id, name=data.definition.name,
                definition_json=data.definition.model_dump_json(),
                revision=1, created_at=utcnow(), updated_at=utcnow())
            db.add(row)
            db.commit()
            db.refresh(row)
            return visible(row, full=True)
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply automation Alembic migration")


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        return visible(row_for(db, user.id, workflow_id), full=True)


@router.put("/workflows/{workflow_id}")
def update_workflow(workflow_id: str, request: Request, data: SaveWorkflow):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = row_for(db, user.id, workflow_id)
        if data.revision != row.revision:
            raise HTTPException(409, "Workflow has changed; reload before updating")
        row.name = data.definition.name
        row.definition_json = data.definition.model_dump_json()
        row.revision += 1
        row.updated_at = utcnow()
        db.commit()
        return visible(row, full=True)


@router.delete("/workflows/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = row_for(db, user.id, workflow_id)
        if db.scalar(select(AutomationRun.id).where(
            AutomationRun.workflow_id == row.id).limit(1)):
            raise HTTPException(409, "Workflow has run history. Archive it instead of deleting")
        if db.scalar(select(AutomationSchedule.id).where(
            AutomationSchedule.workflow_id == row.id).limit(1)):
            raise HTTPException(409, "Disable and delete the workflow schedule first")
        db.delete(row)
        db.commit()
        return Response(status_code=204)


@router.post("/workflows/{workflow_id}/runs", status_code=201)
def run_workflow(workflow_id: str, request: Request, body: RunRequest,
                 idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = row_for(db, user.id, workflow_id)
        if body.live and user.role != "owner":
            raise HTTPException(403, "Only the organization owner may request live execution")
        if body.live and not idempotency_key:
            raise HTTPException(422, "Live runs require an Idempotency-Key header")
        if body.approval:
            raise HTTPException(422, "Approval resume requires a future audited resume API")
        if idempotency_key and (len(idempotency_key) > 100 or len(idempotency_key) < 8):
            raise HTTPException(422, "Invalid idempotency key")
        if idempotency_key:
            existing = db.scalar(select(AutomationRun).where(
                AutomationRun.customer_id == user.id,
                AutomationRun.idempotency_key == idempotency_key))
            if existing:
                if existing.workflow_id != row.id:
                    raise HTTPException(409, "Idempotency key belongs to another workflow")
                return run_visible(existing)
        try:
            return record_run(db, row, input_data=body.input,
                              live=body.live, idempotency_key=idempotency_key)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Duplicate concurrent run key")
        except ValueError as exc:
            raise HTTPException(422, str(exc)[:180])
        except OperationalError:
            raise HTTPException(503, "Apply automation Alembic migration")


@router.get("/workflows/{workflow_id}/runs")
def workflow_runs(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        row = row_for(db, user.id, workflow_id)
        runs = db.scalars(select(AutomationRun)
                          .where(AutomationRun.workflow_id == row.id,
                                 AutomationRun.customer_id == user.id)
                          .order_by(AutomationRun.created_at.desc()).limit(50)).all()
        return {"runs": [run_visible(r) for r in runs]}


@router.get("/control/summary")
def control_summary(request: Request):
    """Customer-scoped operational metrics from persisted run records."""
    with session_factory()() as db:
        user = require_user(request, db)
        workflows = db.scalars(
            select(AutomationWorkflow)
            .where(AutomationWorkflow.customer_id == user.id)
            .order_by(AutomationWorkflow.updated_at.desc()).limit(50)
        ).all()
        recent = db.scalars(
            select(AutomationRun)
            .where(AutomationRun.customer_id == user.id)
            .order_by(AutomationRun.created_at.desc()).limit(100)
        ).all()
        counts = {}
        for run in recent:
            counts[run.status] = counts.get(run.status, 0) + 1
        schedules = db.scalars(
            select(AutomationSchedule)
            .where(AutomationSchedule.customer_id == user.id)
        ).all()
        return {
            "workflow_count": len(workflows),
            "sampled_run_count": len(recent),
            "status_counts": counts,
            "active_schedules": sum(bool(row.enabled) for row in schedules),
            "scope": "latest_100_runs",
            "runs": [run_visible(row) for row in recent[:30]],
            "workflows": [visible(row) for row in workflows],
        }


@router.post("/workflows/{workflow_id}/runs/{run_id}/retry-dry-run", status_code=201)
def retry_dry_run(workflow_id: str, run_id: str, request: Request):
    """Re-run the CURRENT workflow revision in dry-run mode, never replay live effects.

    Historical input is not persisted in run audit logs, so this operation
    explicitly uses an empty input. Callers needing inputs must use the
    regular /runs endpoint with an explicit new payload.
    """
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        workflow = row_for(db, user.id, workflow_id)
        prior = db.scalar(
            select(AutomationRun).where(
                AutomationRun.id == parse_id(run_id),
                AutomationRun.workflow_id == workflow.id,
                AutomationRun.customer_id == user.id,
            )
        )
        if prior is None:
            raise HTTPException(404, "Run not found")
        if prior.mode != "dry_run":
            raise HTTPException(409, "Live runs cannot be retried")
        if prior.status not in {"failed", "step_limit"}:
            raise HTTPException(409, "Only failed dry-runs can be retried")
        definition = WorkflowDefinition.model_validate_json(workflow.definition_json)
        if any(node.kind not in {"trigger", "set", "condition", "transform", "end"}
               for node in definition.nodes):
            raise HTTPException(
                409, "This workflow requires explicit inputs or connector review; "
                     "use the regular dry-run endpoint",
            )
        result = record_run(
            db, workflow, input_data={}, live=False, idempotency_key=None,
        )
        return {**result, "retry_of": prior.id,
                "input_policy": "empty_input_current_revision"}


@router.get("/workflows/{workflow_id}/schedule")
def get_schedule(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        workflow = row_for(db, user.id, workflow_id)
        row = db.scalar(select(AutomationSchedule).where(
            AutomationSchedule.workflow_id == workflow.id,
            AutomationSchedule.customer_id == user.id))
        return {"schedule": ({
            "interval_minutes": row.interval_minutes,
            "enabled": row.enabled,
            "next_run_at": row.next_run_at.isoformat() + "Z",
        } if row else None)}


@router.put("/workflows/{workflow_id}/schedule")
def configure_schedule(workflow_id: str, request: Request, settings: ScheduleRequest):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        workflow = row_for(db, user.id, workflow_id)
        row = db.scalar(select(AutomationSchedule).where(
            AutomationSchedule.workflow_id == workflow.id,
            AutomationSchedule.customer_id == user.id))
        if row is None:
            row = AutomationSchedule(workflow_id=workflow.id, customer_id=user.id)
            db.add(row)
        row.interval_minutes = settings.interval_minutes
        row.enabled = settings.enabled
        row.next_run_at = utcnow() + timedelta(minutes=settings.interval_minutes)
        row.updated_at = utcnow()
        db.commit()
        return {"enabled": row.enabled, "interval_minutes": row.interval_minutes,
                "next_run_at": row.next_run_at.isoformat() + "Z",
                "mode": "dry_run_only", "worker_required": True}


@router.delete("/workflows/{workflow_id}/schedule", status_code=204)
def remove_schedule(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        workflow = row_for(db, user.id, workflow_id)
        row = db.scalar(select(AutomationSchedule).where(
            AutomationSchedule.workflow_id == workflow.id,
            AutomationSchedule.customer_id == user.id))
        if row:
            db.delete(row)
            db.commit()
    return Response(status_code=204)


@router.post("/workflows/{workflow_id}/webhook", status_code=201)
def enable_webhook(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = row_for(db, user.id, workflow_id)
        token = secrets.token_urlsafe(40)
        row.webhook_token_hash = hashlib.sha256(token.encode()).hexdigest()
        db.commit()
        # Token returned only once. Rotating invalidates the previous token.
        return {"url_path": "/hooks/automation/" + row.id,
                "token": token, "mode": "dry_run_only",
                "instructions": "Send X-Omni-Webhook-Token header over HTTPS"}


@router.delete("/workflows/{workflow_id}/webhook", status_code=204)
def disable_webhook(workflow_id: str, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = row_for(db, user.id, workflow_id)
        row.webhook_token_hash = None
        db.commit()
        return Response(status_code=204)


@WEBHOOKS.post("/{workflow_id}", status_code=202)
async def incoming_webhook(workflow_id: str, request: Request,
                           x_omni_webhook_token: str = Header(default="")):
    secure_request(request)
    if len(x_omni_webhook_token) < 40 or len(x_omni_webhook_token) > 100:
        raise HTTPException(404, "Webhook unavailable")
    try:
        declared_length = int(request.headers.get("content-length", "0") or "0")
    except ValueError:
        raise HTTPException(400, "Invalid Content-Length")
    if declared_length < 0 or declared_length > 16000:
        raise HTTPException(413, "Webhook payload too large")
    # Limit streaming bytes even if the client omits Content-Length.
    chunks = bytearray()
    async for part in request.stream():
        chunks.extend(part)
        if len(chunks) > 16000:
            raise HTTPException(413, "Webhook payload too large")
    try:
        data = json.loads(chunks)
        if not isinstance(data, dict):
            raise ValueError("Payload must be an object")
        bounded(data)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(422, "Invalid JSON webhook payload")
    with session_factory()() as db:
        row = db.get(AutomationWorkflow, parse_id(workflow_id))
        if not row or not row.webhook_token_hash:
            raise HTTPException(404, "Webhook unavailable")
        supplied = hashlib.sha256(x_omni_webhook_token.encode()).hexdigest()
        if not hmac.compare_digest(supplied, row.webhook_token_hash):
            raise HTTPException(404, "Webhook unavailable")
        try:
            result = record_run(db, row, input_data=data, live=False, idempotency_key=None)
        except (ValueError, OperationalError):
            raise HTTPException(422, "Workflow failed to accept webhook input")
    return {"accepted": True, "run_id": result["id"], "status": result["status"]}
