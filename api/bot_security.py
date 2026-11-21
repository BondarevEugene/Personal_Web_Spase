"""Secure Telegram bot ownership, credentials and customer-specific invitations.

Policy:
- owner may store/rotate/revoke and explicitly verify token
- invited registered user accepts a single-use, expiring invitation
- invited users can only read minimal shared bot metadata (not graph, token,
  deployment control, billing or infrastructure) until those APIs implement
  dedicated grant checks
- every mutation is CSRF protected and audited without sensitive values
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from automation import bot_vault
from portal.db import session_factory
from portal.models import (BotAccessGrant, BotAccessInvitation, BotCredential,
                           BotSecurityAudit, BuilderProject, Customer, utcnow)
from portal.routes import current_customer
from portal.security import secure_request, token_hash, verify_csrf

router = APIRouter(prefix="/api/v1/bot-security", tags=["Bot Security & Access"])


class TelegramSecret(BaseModel):
    token: str = Field(min_length=35, max_length=116)


class InvitationRequest(BaseModel):
    username: str = Field(min_length=4, max_length=32)
    role: str = Field(pattern=r"^(viewer|operator)$")


class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=200)


def current(request: Request, db):
    secure_request(request)
    user = current_customer(request, db)
    if not user:
        raise HTTPException(401, "Sign in to access Bot Lab")
    return user


def csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError):
        raise HTTPException(404, "Bot project not found")


def owned(db, user_id: str, project_id: str) -> BuilderProject:
    row = db.scalar(select(BuilderProject).where(
        BuilderProject.id == uuid(project_id),
        BuilderProject.customer_id == user_id,
    ))
    if row is None:
        raise HTTPException(404, "Bot project not found")
    return row


def audit(db, project_id: str, actor: str, action: str, target: str | None = None):
    db.add(BotSecurityAudit(project_id=project_id, actor_id=actor,
                            event=action, target_customer_id=target, created_at=utcnow()))


def secret_status(row: BotCredential | None) -> dict:
    return {
        "configured": row is not None,
        "verified": bool(row and row.verified_at),
        "username": row.verified_username if row else None,
        "bot_id": row.verified_bot_id if row else None,
        "verified_at": row.verified_at.isoformat() + "Z" if row and row.verified_at else None,
        "updated_at": row.rotated_at.isoformat() + "Z" if row else None,
    }


@router.get("/capabilities")
def capabilities():
    return {
        "vault_configured": bot_vault.readiness(),
        "secrets_returned_to_browser": False,
        "invitation_lifetime_hours": 24,
        "roles": {
            "owner": "secret and access management for own bot only",
            "operator": "shared metadata only; live operations require future explicit API policy",
            "viewer": "shared bot metadata only",
        },
        "cross_account_graph_access": False,
        "live_telegram_deployment": False,
    }


@router.get("/bots/{project_id}/credential")
def get_credential_status(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        project = owned(db, user.id, project_id)
        row = db.scalar(select(BotCredential).where(
            BotCredential.project_id == project.id,
            BotCredential.owner_id == user.id,
        ))
        return {"project_id": project.id, **secret_status(row),
                "vault_configured": bot_vault.readiness()}


@router.put("/bots/{project_id}/credential")
def store_credential(project_id: str, body: TelegramSecret, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        try:
            encrypted, fingerprint = bot_vault.encrypt_token(user.id, project.id, body.token)
        except bot_vault.BotVaultUnavailable:
            raise HTTPException(503, "Bot Vault is not configured")
        except ValueError:
            raise HTTPException(422, "Invalid BotFather token format")
        now = utcnow()
        row = db.scalar(select(BotCredential).where(
            BotCredential.project_id == project.id,
            BotCredential.owner_id == user.id,
        ))
        if row is None:
            row = BotCredential(project_id=project.id, owner_id=user.id, created_at=now)
            db.add(row)
            event = "credential_added"
        else:
            event = "credential_rotated"
        row.ciphertext = encrypted
        row.fingerprint = fingerprint
        row.verified_at = None
        row.verified_username = None
        row.verified_bot_id = None
        row.rotated_at = now
        audit(db, project.id, user.id, event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Credential already changed concurrently; refresh")
        response = {"project_id": project.id, **secret_status(row)}
        return response


@router.post("/bots/{project_id}/credential/verify")
def verify_credential(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        row = db.scalar(select(BotCredential).where(
            BotCredential.project_id == project.id,
            BotCredential.owner_id == user.id,
        ))
        if not row:
            raise HTTPException(409, "Add BotFather token first")
        try:
            token = bot_vault.decrypt_token(user.id, project.id, row.ciphertext)
            identity = bot_vault.telegram_get_me(token)
        except bot_vault.BotVaultUnavailable:
            raise HTTPException(503, "Bot Vault is unavailable")
        except bot_vault.TelegramVerificationError:
            audit(db, project.id, user.id, "telegram_verification_failed")
            db.commit()
            raise HTTPException(422, "Telegram identity check failed")
        row.verified_bot_id = identity["bot_id"]
        row.verified_username = identity["username"]
        row.verified_at = utcnow()
        audit(db, project.id, user.id, "telegram_verified")
        db.commit()
        return {"project_id": project.id, **secret_status(row)}


@router.delete("/bots/{project_id}/credential", status_code=204)
def revoke_credential(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        row = db.scalar(select(BotCredential).where(
            BotCredential.project_id == project.id,
            BotCredential.owner_id == user.id,
        ))
        if row:
            db.delete(row)
            audit(db, project.id, user.id, "credential_deleted")
        db.commit()
    return Response(status_code=204)


@router.post("/bots/{project_id}/invitations", status_code=201)
def create_invitation(project_id: str, body: InvitationRequest, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        target = db.scalar(select(Customer).where(Customer.username == body.username.strip().lower()))
        if target is None or not target.is_active or target.id == user.id:
            raise HTTPException(422, "Specify an active, different OmniFactory username")
        already = db.scalar(select(BotAccessGrant.id).where(
            BotAccessGrant.project_id == project.id, BotAccessGrant.grantee_id == target.id))
        if already:
            raise HTTPException(409, "User already has access; revoke first to change role")
        pending = db.scalar(select(func.count()).select_from(BotAccessInvitation).where(
            BotAccessInvitation.project_id == project.id,
            BotAccessInvitation.owner_id == user.id,
            BotAccessInvitation.revoked_at.is_(None),
            BotAccessInvitation.consumed_at.is_(None),
            BotAccessInvitation.expires_at > utcnow(),
        )) or 0
        if pending >= 10:
            raise HTTPException(429, "Too many outstanding invitations for this bot")
        raw = secrets.token_urlsafe(32)
        invite = BotAccessInvitation(
            project_id=project.id, owner_id=user.id, invited_customer_id=target.id,
            role=body.role, token_hash=token_hash(raw),
            expires_at=utcnow() + timedelta(hours=24), created_at=utcnow())
        db.add(invite)
        audit(db, project.id, user.id, "invitation_created", target.id)
        db.commit()
        return {
            "id": invite.id, "username": target.username, "role": invite.role,
            "expires_at": invite.expires_at.isoformat() + "Z",
            "one_time_token": raw,
            "note": "Shown once. Share privately with the specific registered user.",
        }


@router.post("/invitations/accept")
def accept_invitation(request: Request, body: InvitationAccept):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        if not 32 <= len(body.token) <= 200:
            raise HTTPException(422, "Invalid invitation token")
        now = utcnow()
        # Compare-and-swap for one-time acceptance; target bound to login.
        row = db.scalar(select(BotAccessInvitation).where(
            BotAccessInvitation.token_hash == token_hash(body.token),
            BotAccessInvitation.invited_customer_id == user.id,
            BotAccessInvitation.consumed_at.is_(None),
            BotAccessInvitation.revoked_at.is_(None),
            BotAccessInvitation.expires_at > now,
        ))
        if not row:
            raise HTTPException(404, "Invitation unavailable")
        claim = db.execute(update(BotAccessInvitation).where(
            BotAccessInvitation.id == row.id,
            BotAccessInvitation.invited_customer_id == user.id,
            BotAccessInvitation.consumed_at.is_(None),
            BotAccessInvitation.revoked_at.is_(None),
            BotAccessInvitation.expires_at > now,
        ).values(consumed_at=now))
        if claim.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "Invitation already used")
        if db.scalar(select(BotAccessGrant.id).where(
            BotAccessGrant.project_id == row.project_id,
            BotAccessGrant.grantee_id == user.id,
        )):
            db.rollback()
            raise HTTPException(409, "Access already exists")
        db.add(BotAccessGrant(project_id=row.project_id, owner_id=row.owner_id,
                              grantee_id=user.id, role=row.role, created_at=now))
        audit(db, row.project_id, user.id, "invitation_accepted", user.id)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Invitation already accepted")
        return {"project_id": row.project_id, "role": row.role, "accepted": True}


@router.get("/bots/{project_id}/invitations")
def list_invitations(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        project = owned(db, user.id, project_id)
        rows = db.execute(select(BotAccessInvitation, Customer).join(
            Customer, Customer.id == BotAccessInvitation.invited_customer_id
        ).where(
            BotAccessInvitation.project_id == project.id,
            BotAccessInvitation.owner_id == user.id,
            BotAccessInvitation.consumed_at.is_(None),
            BotAccessInvitation.revoked_at.is_(None),
            BotAccessInvitation.expires_at > utcnow(),
        ).limit(30)).all()
        return {"invitations": [
            {"id": invite.id, "username": target.username, "role": invite.role,
             "expires_at": invite.expires_at.isoformat() + "Z"}
            for invite, target in rows]}


@router.delete("/bots/{project_id}/invitations/{invitation_id}", status_code=204)
def cancel_invitation(project_id: str, invitation_id: UUID, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        row = db.scalar(select(BotAccessInvitation).where(
            BotAccessInvitation.id == str(invitation_id),
            BotAccessInvitation.project_id == project.id,
            BotAccessInvitation.owner_id == user.id,
            BotAccessInvitation.consumed_at.is_(None),
            BotAccessInvitation.revoked_at.is_(None),
        ))
        if not row:
            raise HTTPException(404, "Invitation not found")
        row.revoked_at = utcnow()
        audit(db, project.id, user.id, "invitation_cancelled", row.invited_customer_id)
        db.commit()
    return Response(status_code=204)


@router.get("/bots/{project_id}/access")
def list_access(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        project = owned(db, user.id, project_id)
        grants = db.execute(select(BotAccessGrant, Customer).join(
            Customer, Customer.id == BotAccessGrant.grantee_id
        ).where(BotAccessGrant.project_id == project.id,
                BotAccessGrant.owner_id == user.id)).all()
        return {"project_id": project.id, "members": [
            {"id": grant.grantee_id, "username": grantee.username,
             "role": grant.role, "created_at": grant.created_at.isoformat() + "Z"}
            for grant, grantee in grants]}


@router.delete("/bots/{project_id}/access/{grantee_id}", status_code=204)
def revoke_access(project_id: str, grantee_id: UUID, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        csrf(request)
        project = owned(db, user.id, project_id)
        grant = db.scalar(select(BotAccessGrant).where(
            BotAccessGrant.project_id == project.id,
            BotAccessGrant.owner_id == user.id,
            BotAccessGrant.grantee_id == str(grantee_id),
        ))
        if not grant:
            raise HTTPException(404, "Access grant not found")
        db.delete(grant)
        audit(db, project.id, user.id, "access_revoked", str(grantee_id))
        db.commit()
    return Response(status_code=204)


@router.get("/shared")
def shared_bots(request: Request):
    with session_factory()() as db:
        user = current(request, db)
        rows = db.execute(select(BotAccessGrant, BuilderProject).join(
            BuilderProject, BuilderProject.id == BotAccessGrant.project_id
        ).where(BotAccessGrant.grantee_id == user.id).limit(100)).all()
        return {"bots": [
            {"id": project.id, "name": project.name, "role": grant.role,
             "owner_id": grant.owner_id,
             "updated_at": project.updated_at.isoformat() + "Z"}
            for grant, project in rows]}


@router.get("/bots/{project_id}/audit")
def list_audit(project_id: str, request: Request):
    with session_factory()() as db:
        user = current(request, db)
        project = owned(db, user.id, project_id)
        events = db.scalars(select(BotSecurityAudit).where(
            BotSecurityAudit.project_id == project.id
        ).order_by(BotSecurityAudit.created_at.desc()).limit(100)).all()
        return {"events": [
            {"event": e.event, "actor_id": e.actor_id,
             "target_customer_id": e.target_customer_id,
             "created_at": e.created_at.isoformat() + "Z"} for e in events]}
