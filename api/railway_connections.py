"""Railway account connections: OAuth authorization, refresh and local disconnect.

No deployment mutation is exposed. Browser never receives provider tokens.
"""
from __future__ import annotations

import hmac
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError

from automation import railway_oauth as oauth
from portal.db import session_factory
from portal.models import CloudOAuthAttempt, CloudOAuthConnection, utcnow
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/api/v1/cloud/railway", tags=["Railway Connections"])
UI = "/cloud/deploy"


def require_customer(request: Request, db):
    secure_request(request)
    customer = current_customer(request, db)
    if not customer:
        raise HTTPException(401, "Log in to OmniFactory before connecting Railway")
    return customer


def require_csrf(request: Request):
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))


def row_info(connection: CloudOAuthConnection) -> dict:
    return {
        "provider": "railway", "connected": True,
        "account_name": connection.remote_name,
        "subject": connection.remote_subject,
        "scopes": connection.scopes.split(),
        "expires_at": connection.expires_at.isoformat() + "Z",
        "refresh_available": bool(connection.refresh_ciphertext),
    }


@router.get("/status")
def status(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        row = db.scalar(select(CloudOAuthConnection).where(
            CloudOAuthConnection.customer_id == user.id,
            CloudOAuthConnection.provider == "railway"))
        return {"connected": False, "configuration": oauth.readiness()} if row is None else {
            **row_info(row), "configuration": oauth.readiness()}


@router.post("/authorize")
def authorize(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        require_csrf(request)
        try:
            oauth.settings()
            state, verifier, challenge = oauth.new_attempt()
            row = CloudOAuthAttempt(
                customer_id=user.id, provider="railway",
                state_hash=oauth.state_hash(state),
                verifier_ciphertext=oauth.encrypt(verifier),
                expires_at=utcnow() + __import__("datetime").timedelta(minutes=10),
                created_at=utcnow(),
            )
            db.add(row)
            db.commit()
            return {"authorization_url": oauth.authorize_url(state, challenge),
                    "expires_in": 600}
        except oauth.OAuthConfigurationError:
            raise HTTPException(503, "Railway OAuth is not configured by operator")
        except OperationalError:
            db.rollback()
            raise HTTPException(503, "Apply portal OAuth migration")


@router.get("/callback", name="railway_oauth_callback")
def callback(request: Request, code: str | None = None, state: str | None = None,
             error: str | None = None, iss: str | None = None):
    # The callback only uses server-generated state and the current portal
    # session. No token ever appears in a redirect URL.
    with session_factory()() as db:
        user = require_customer(request, db)
        if error:
            return RedirectResponse(UI + "?railway=denied", status_code=303)
        if not code or not state or len(code) > 2048 or len(state) > 200:
            raise HTTPException(400, "Invalid Railway callback")
        if iss is not None and not hmac.compare_digest(iss, oauth.ISSUER):
            raise HTTPException(400, "Unexpected OAuth issuer")
        digest = oauth.state_hash(state)
        attempt = db.scalar(select(CloudOAuthAttempt).where(
            CloudOAuthAttempt.customer_id == user.id,
            CloudOAuthAttempt.provider == "railway",
            CloudOAuthAttempt.state_hash == digest))
        if not attempt or attempt.expires_at <= utcnow():
            raise HTTPException(400, "OAuth state expired or not found")
        # Consume state BEFORE exchanging short-lived code; atomic claim blocks
        # replay and parallel callbacks.
        taken = db.execute(update(CloudOAuthAttempt).where(
            CloudOAuthAttempt.id == attempt.id,
            CloudOAuthAttempt.consumed_at.is_(None),
            CloudOAuthAttempt.expires_at > utcnow(),
        ).values(consumed_at=utcnow()))
        db.commit()
        if taken.rowcount != 1:
            raise HTTPException(400, "OAuth authorization already used")
        try:
            verifier = oauth.decrypt(attempt.verifier_ciphertext)
            tokens = oauth.exchange_code(code, verifier)
            account = oauth.profile(tokens["access_token"])
            access_encrypted = oauth.encrypt(tokens["access_token"])
            refresh_encrypted = (oauth.encrypt(tokens["refresh_token"])
                                 if tokens.get("refresh_token") else None)
        except (oauth.OAuthProviderError, oauth.OAuthConfigurationError, ValueError):
            return RedirectResponse(UI + "?railway=failed", status_code=303)
        existing = db.scalar(select(CloudOAuthConnection).where(
            CloudOAuthConnection.customer_id == user.id,
            CloudOAuthConnection.provider == "railway"))
        now = utcnow()
        if existing is None:
            existing = CloudOAuthConnection(customer_id=user.id, provider="railway",
                                            created_at=now)
            db.add(existing)
        existing.remote_subject = str(account["sub"])[:200]
        existing.remote_name = str(account.get("name") or "")[:200]
        existing.scopes = str(tokens.get("scope", ""))[:2000]
        existing.access_ciphertext = access_encrypted
        # If scope changes, old refresh credentials must not be reused.
        existing.refresh_ciphertext = refresh_encrypted
        existing.expires_at = oauth.expiry(tokens["expires_in"])
        existing.updated_at = now
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Concurrent Railway authorization; reconnect")
        return RedirectResponse(UI + "?railway=connected", status_code=303)


@router.post("/refresh")
def refresh(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        require_csrf(request)
        row = db.scalar(select(CloudOAuthConnection).where(
            CloudOAuthConnection.customer_id == user.id,
            CloudOAuthConnection.provider == "railway"))
        if not row or not row.refresh_ciphertext:
            raise HTTPException(409, "Reconnect Railway to enable offline access")
        try:
            tokens = oauth.refresh_token(oauth.decrypt(row.refresh_ciphertext))
            # Rotate refresh token when Railway returns it.
            access = oauth.encrypt(tokens["access_token"])
            rotated = oauth.encrypt(tokens["refresh_token"]) if tokens.get("refresh_token") else None
        except (oauth.OAuthConfigurationError, oauth.OAuthProviderError, ValueError):
            raise HTTPException(502, "Railway token refresh failed; reconnect if access was revoked")
        row.access_ciphertext = access
        if rotated:
            row.refresh_ciphertext = rotated
        row.expires_at = oauth.expiry(tokens["expires_in"])
        row.updated_at = utcnow()
        if tokens.get("scope"):
            row.scopes = str(tokens["scope"])[:2000]
        db.commit()
        return row_info(row)


@router.delete("/disconnect", status_code=204)
def disconnect(request: Request):
    with session_factory()() as db:
        user = require_customer(request, db)
        require_csrf(request)
        row = db.scalar(select(CloudOAuthConnection).where(
            CloudOAuthConnection.customer_id == user.id,
            CloudOAuthConnection.provider == "railway"))
        if row:
            db.delete(row)
        # Invalidate outstanding grants initiated by this customer too.
        for attempt in db.scalars(select(CloudOAuthAttempt).where(
            CloudOAuthAttempt.customer_id == user.id,
            CloudOAuthAttempt.provider == "railway",
            CloudOAuthAttempt.consumed_at.is_(None))).all():
            attempt.consumed_at = utcnow()
        db.commit()
    from fastapi import Response
    return Response(status_code=204)
