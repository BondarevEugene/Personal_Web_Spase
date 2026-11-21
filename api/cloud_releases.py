"""Immutable release review for protected OmniFactory Bot Lab.

Owner-only; no permission inherited from invitation roles. No provider
mutations, no secret reads in API responses, no actual financial approval.
"""
from __future__ import annotations

import re
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from automation.deployment import DeploymentSpec, build_plan
from automation.release_gate import (
    allowed_image, release_preview, review_sha256, scenario_sha256,
)
from portal.db import session_factory
from portal.models import (
    BotCredential, BuilderProject, CloudDeployment, CloudOAuthConnection,
    CloudRailwayBinding, CloudReleaseReview, BotSecurityAudit, utcnow,
)
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/cloud/releases", tags=["Managed Cloud Release Gate"])
KEY = re.compile(r"^[A-Za-z0-9_:-]{8,100}$")


class ReviewRequest(BaseModel):
    bot_project_id: UUID
    cloud_plan_id: UUID
    confirmation: str


def require_user(request: Request, db):
    secure_request(request)
    user = current_customer(request, db)
    if user is None:
        raise HTTPException(401, "Sign in as the bot owner")
    return user


def csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def snapshot(db, owner_id: str, bot_id: str, plan_id: str):
    bot = db.scalar(select(BuilderProject).where(
        BuilderProject.id == bot_id, BuilderProject.customer_id == owner_id))
    plan = db.scalar(select(CloudDeployment).where(
        CloudDeployment.id == plan_id, CloudDeployment.customer_id == owner_id))
    if bot is None or plan is None:
        raise HTTPException(404, "Bot or cloud plan not found in this account")
    spec = DeploymentSpec.model_validate_json(plan.manifest_json)
    if spec.runtime != "telegram_aiogram":
        raise HTTPException(409, "This release gate supports Telegram bots only")
    if plan.status != "planned" or build_plan(spec).manifest_sha256 != plan.manifest_sha256:
        raise HTTPException(409, "Cloud plan no longer matches its immutable manifest")
    credential = db.scalar(select(BotCredential).where(
        BotCredential.project_id == bot.id, BotCredential.owner_id == owner_id))
    # Authentication proof is a previous getMe check, not a token returned here.
    token_ok = bool(credential and credential.verified_at and credential.verified_bot_id)
    conn = db.scalar(select(CloudOAuthConnection).where(
        CloudOAuthConnection.customer_id == owner_id,
        CloudOAuthConnection.provider == "railway"))
    oauth_ok = bool(conn and conn.expires_at > utcnow())
    binding = db.scalar(select(CloudRailwayBinding).where(
        CloudRailwayBinding.deployment_id == plan.id,
        CloudRailwayBinding.customer_id == owner_id))
    binding_ok = bool(binding and binding.verified_at)
    gate = release_preview(spec=spec, bot_owned=True,
        token_verified=token_ok, binding_verified=binding_ok,
        oauth_current=oauth_ok)
    return bot, plan, spec, credential, gate


def serialize(row: CloudReleaseReview, valid: bool | None = None):
    return {
        "id": row.id, "bot_project_id": row.bot_project_id,
        "cloud_plan_id": row.cloud_plan_id, "status": row.status,
        "artifact_image": row.artifact_image,
        "budget_cap_usd": row.budget_cap_usd,
        "review_sha256": row.review_hash,
        "created_at": row.created_at.isoformat() + "Z",
        "expires_at": row.expires_at.isoformat() + "Z",
        "still_valid": valid,
        "billable_actions_permitted": False,
    }


@router.get("/capabilities")
def capabilities():
    return {"review_intent": True, "immutable_image_required": True,
            "estimated_spend_available": False,
            "live_railway_mutations_enabled": False,
            "client_grants_can_publish": False}


@router.get("/preflight/{bot_id}/{plan_id}")
def preflight(bot_id: UUID, plan_id: UUID, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        bot, plan, spec, credential, gate = snapshot(
            db, user.id, str(bot_id), str(plan_id))
        return {"bot_name": bot.name, "plan_name": plan.name,
                "bot_project_id": bot.id, "cloud_plan_id": plan.id,
                **gate}


@router.post("/reviews", status_code=201)
def request_review(request: Request, body: ReviewRequest):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        key = request.headers.get("Idempotency-Key", "")
        if not KEY.fullmatch(key):
            raise HTTPException(422, "Idempotency-Key 8-100 safe characters required")
        if body.confirmation != "REQUEST RELEASE REVIEW":
            raise HTTPException(422, "Confirmation must be REQUEST RELEASE REVIEW")
        bot, plan, spec, credential, gate = snapshot(
            db, user.id, str(body.bot_project_id), str(body.cloud_plan_id))
        if not gate["ready_for_review"] or not credential:
            raise HTTPException(409, "Resolve release preflight prerequisites first")
        digest = scenario_sha256(bot.scenario_json)
        review_hash = review_sha256(
            owner_id=user.id, bot_id=bot.id, plan_id=plan.id,
            plan_hash=plan.manifest_sha256,
            credential_fingerprint=credential.fingerprint,
            revision_hash=digest, image=gate["approved_image"],
            budget=spec.max_monthly_usd)
        prev = db.scalar(select(CloudReleaseReview).where(
            CloudReleaseReview.owner_id == user.id,
            CloudReleaseReview.request_key == key))
        if prev:
            if (prev.review_hash != review_hash or prev.cancelled_at
                    or prev.expires_at <= utcnow()):
                raise HTTPException(409, "Idempotency key reused, expired or review cancelled")
            return serialize(prev, True)
        now = utcnow()
        row = CloudReleaseReview(
            owner_id=user.id, bot_project_id=bot.id, cloud_plan_id=plan.id,
            request_key=key, artifact_image=gate["approved_image"],
            plan_hash=plan.manifest_sha256,
            credential_fingerprint=credential.fingerprint,
            revision_hash=digest, review_hash=review_hash,
            budget_cap_usd=spec.max_monthly_usd,
            status="review_requested", created_at=now,
            expires_at=now + timedelta(hours=24),
        )
        db.add(row)
        db.add(BotSecurityAudit(
            project_id=bot.id, actor_id=user.id,
            event="release_review_requested", created_at=now))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Concurrent review request; refresh")
        return serialize(row, True)


@router.get("/reviews")
def list_reviews(request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        rows = db.scalars(select(CloudReleaseReview).where(
            CloudReleaseReview.owner_id == user.id,
        ).order_by(CloudReleaseReview.created_at.desc()).limit(50)).all()
        return {"reviews": [serialize(row) for row in rows]}


@router.get("/reviews/{review_id}")
def read_review(review_id: UUID, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        row = db.scalar(select(CloudReleaseReview).where(
            CloudReleaseReview.id == str(review_id),
            CloudReleaseReview.owner_id == user.id))
        if row is None:
            raise HTTPException(404, "Review not found")
        current = False
        if row.cancelled_at is None and row.expires_at > utcnow():
            try:
                bot, plan, spec, cred, gate = snapshot(
                    db, user.id, row.bot_project_id, row.cloud_plan_id)
                current = bool(cred and gate["ready_for_review"] and
                    review_sha256(
                        owner_id=user.id, bot_id=bot.id, plan_id=plan.id,
                        plan_hash=plan.manifest_sha256,
                        credential_fingerprint=cred.fingerprint,
                        revision_hash=scenario_sha256(bot.scenario_json),
                        image=gate["approved_image"],
                        budget=spec.max_monthly_usd) == row.review_hash)
            except (HTTPException, ValueError):
                current = False
        return serialize(row, current)


@router.post("/reviews/{review_id}/cancel")
def cancel_review(review_id: UUID, request: Request):
    with session_factory()() as db:
        user = require_user(request, db)
        csrf(request)
        row = db.scalar(select(CloudReleaseReview).where(
            CloudReleaseReview.id == str(review_id),
            CloudReleaseReview.owner_id == user.id))
        if row is None:
            raise HTTPException(404, "Review not found")
        if row.cancelled_at is None:
            row.cancelled_at = utcnow()
            row.status = "cancelled"
            db.add(BotSecurityAudit(project_id=row.bot_project_id,
                actor_id=user.id, event="release_review_cancelled",
                created_at=utcnow()))
            db.commit()
        return serialize(row, False)
