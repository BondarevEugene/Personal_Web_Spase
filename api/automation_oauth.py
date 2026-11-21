"""Authenticated OAuth connect/callback for Google and Meta.

Only a tenant owner can initiate and complete authorization. Provider responses
and tokens are never returned to the browser or written to audit events.
"""
from __future__ import annotations

import json

import httpx

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from api.automation_connections import connection_for, csrf, owner
from automation.connection_vault import seal
from automation.oauth_providers import CONFIG, authorization_url, exchange_code
from automation.oauth_state import consume_pkce_state, issue_pkce_state
from portal.db import session_factory
from portal.models import (
    AutomationConnectionEvent,
    AutomationCredential,
    utcnow,
)

router = APIRouter(prefix="/api/v1/automation/oauth", tags=["Automation OAuth"])


@router.post("/{connection_id}/start")
def start(connection_id: str, request: Request):
    with session_factory()() as db:
        user = owner(request, db)
        csrf(request)
        connection = connection_for(db, user.id, connection_id)
        if connection.provider not in CONFIG or connection.status == "disconnected":
            raise HTTPException(409, "OAuth not available for this connection")
        # Check provider credentials before persisting state.
        from automation.oauth_providers import settings
        try:
            settings(connection.provider)
        except RuntimeError:
            raise HTTPException(503, "OAuth provider is not configured")
        nonce, challenge = issue_pkce_state(
            db, customer_id=user.id, connection_id=connection.id)
        return {"authorization_url": authorization_url(connection.provider, nonce, challenge),
                "expires_in_seconds": 600}


@router.get("/callback")
def callback(request: Request, state: str = "", code: str = "", error: str = ""):
    with session_factory()() as db:
        user = owner(request, db)
        if error:
            raise HTTPException(400, "Provider declined authorization")
        if not code or len(code) > 4096:
            raise HTTPException(400, "Invalid authorization response")
        redeemed = consume_pkce_state(db, nonce=state, customer_id=user.id)
        if redeemed is None:
            raise HTTPException(403, "Invalid or expired OAuth state")
        connection_id, verifier = redeemed
        connection = connection_for(db, user.id, connection_id)
        if connection.provider not in CONFIG or connection.status == "disconnected":
            raise HTTPException(409, "Connection is not eligible")
        try:
            tokens = exchange_code(connection.provider, code, verifier)
            encrypted = seal(json.dumps(tokens, separators=(",", ":"))).ciphertext
        except (httpx.HTTPError, ValueError, TypeError, RuntimeError, KeyError):
            # Never disclose provider errors or token payloads.
            raise HTTPException(502, "OAuth exchange failed")
        credential = db.scalar(select(AutomationCredential).where(
            AutomationCredential.connection_id == connection.id,
            AutomationCredential.customer_id == user.id,
        ))
        if credential is None:
            credential = AutomationCredential(
                connection_id=connection.id, customer_id=user.id,
                ciphertext=encrypted)
            db.add(credential)
        else:
            credential.ciphertext = encrypted
            credential.updated_at = utcnow()
        connection.status = "authorized_unverified"
        connection.updated_at = utcnow()
        db.add(AutomationConnectionEvent(
            connection_id=connection.id, customer_id=user.id,
            actor_id=user.id, action="oauth_authorized",
        ))
        db.commit()
        return {"connection_id": connection.id, "status": "authorized_unverified",
                "permissions_verified": False}
