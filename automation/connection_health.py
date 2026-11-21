"""Provider-backed connection diagnostics; no secrets in responses or logs."""
from __future__ import annotations

import json

import httpx
from sqlalchemy import select

from automation.connection_vault import unseal
from portal.models import AutomationCredential

GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"
META_ME = "https://graph.facebook.com/v22.0/me"


def probe(provider: str, token: str) -> dict:
    """Only fixed trusted provider endpoints; never accept a caller-supplied URL."""
    if provider in {"google_docs", "google_sheets"}:
        url = GOOGLE_TOKENINFO
        params = {"access_token": token}
    elif provider in {"facebook_page", "instagram"}:
        url = META_ME
        params = {"fields": "id", "access_token": token}
    else:
        return {"health": "unsupported", "permissions_verified": False}
    try:
        with httpx.Client(timeout=8, follow_redirects=False) as client:
            response = client.get(url, params=params)
        if response.status_code in {400, 401, 403}:
            return {"health": "reauthorization_required", "permissions_verified": False}
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return {"health": "provider_error", "permissions_verified": False}
        if provider.startswith("google_"):
            from automation.oauth_providers import CONFIG
            expected_scope = CONFIG[provider][3]
            scopes = set(payload.get("scope", "").split())
            return {"health": "healthy" if expected_scope in scopes else "missing_permissions",
                    "permissions_verified": expected_scope in scopes}
        # Meta /me confirms token identity, not granular page or Instagram permissions.
        return {"health": "authorized_unverified",
                "permissions_verified": False}
    except (httpx.HTTPError, ValueError, TypeError):
        return {"health": "provider_unavailable", "permissions_verified": False}


def check_connection(db, connection):
    if connection.status == "disconnected":
        return {"health": "disconnected", "permissions_verified": False}
    credential = db.scalar(select(AutomationCredential).where(
        AutomationCredential.connection_id == connection.id,
        AutomationCredential.customer_id == connection.customer_id,
    ))
    if credential is None:
        return {"health": "not_configured", "permissions_verified": False}
    try:
        token = json.loads(unseal(credential.ciphertext))["access_token"]
        if not isinstance(token, str) or not token:
            return {"health": "credential_invalid", "permissions_verified": False}
    except (ValueError, KeyError, TypeError, UnicodeError):
        return {"health": "credential_invalid", "permissions_verified": False}
    return probe(connection.provider, token)
