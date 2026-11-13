"""OmniFactory Automation API: authenticated definitions, dry-runs and audits.

Public webhooks are opt-in, per-workflow token-protected and dry-run-only.
Live connector execution must be manually requested by an authenticated owner
and explicitly enabled by the operator. No background task is silently started.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from automation.engine import RunRequest, WorkflowDefinition, bounded, execute
from portal.db import session_factory
from portal.models import AutomationRun, AutomationWorkflow, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/automation", tags=["Automation Engine"])
WEBHOOKS = APIRouter(prefix="/hooks/automation", tags=["Automation Webhooks"])


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
    bounded(input_data)
    result = execute(WorkflowDefinition.model_validate_json(workflow.definition_json),
                     input_data, live=live)
    row = AutomationRun(
        workflow_id=workflow.id, customer_id=workflow.customer_id,
        workflow_revision=workflow.revision, status=result.status,
        mode="live" if live else "dry_run",
        idempotency_key=idempotency_key,
        trace_json=json.dumps(result.trace, ensure_ascii=False),
        created_at=utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    return run_visible(row)


@router.get("/catalog")
def catalog():
    return {"version": "v1", "supported": [
        "trigger", "set", "condition", "transform", "http", "google_docs",
        "google_sheets", "facebook_page", "instagram", "approval", "end"],
        "default_mode": "dry_run",
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
                          "cron scheduler", "arbitrary Python execution"]}


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
    if int(request.headers.get("content-length", "0") or "0") > 16000:
        raise HTTPException(413, "Webhook payload too large")
    body = await request.body()
    if len(body) > 16000:
        raise HTTPException(413, "Webhook payload too large")
    try:
        data = json.loads(body)
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
