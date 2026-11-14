"""OAuth 2.0 Authorization Code + S256 PKCE for Railway web connections.

No provider password is accepted. Fernet encryption keys and client credentials
must be injected by the deployment operator; no default production keys.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken

from portal.models import utcnow

AUTH_URL = "https://backboard.railway.com/oauth/auth"
TOKEN_URL = "https://backboard.railway.com/oauth/token"
ME_URL = "https://backboard.railway.com/oauth/me"
ISSUER = "https://backboard.railway.com"
SCOPES = "openid email profile offline_access workspace:member project:member"


class OAuthConfigurationError(RuntimeError):
    pass


class OAuthProviderError(RuntimeError):
    pass


def settings() -> tuple[str, str, str]:
    client_id = os.environ.get("OMNI_RAILWAY_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("OMNI_RAILWAY_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("OMNI_RAILWAY_OAUTH_REDIRECT_URI", "").strip()
    if not all((client_id, client_secret, redirect_uri)):
        raise OAuthConfigurationError("Railway OAuth client ID, secret and redirect URI required")
    parsed = urlparse(redirect_uri)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        raise OAuthConfigurationError("Redirect URI must be HTTPS except loopback development")
    if (not parsed.hostname or parsed.username or parsed.password or
            parsed.fragment or parsed.query or parsed.path != "/api/v1/cloud/railway/callback"):
        raise OAuthConfigurationError("Invalid configured Railway callback URI")
    return client_id, client_secret, redirect_uri


def cipher() -> Fernet:
    key = os.environ.get("OMNI_CLOUD_OAUTH_FERNET_KEY", "")
    if not key:
        raise OAuthConfigurationError("Set OMNI_CLOUD_OAUTH_FERNET_KEY on all web workers")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeError) as exc:
        raise OAuthConfigurationError("Invalid Fernet key") from exc


def encrypt(value: str) -> str:
    if not value or len(value) > 8192:
        raise ValueError("Invalid provider secret")
    return cipher().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str) -> str:
    try:
        return cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise OAuthConfigurationError("Stored token cannot be decrypted") from exc


def new_attempt() -> tuple[str, str, str]:
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return state, verifier, challenge


def state_hash(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def authorize_url(state: str, challenge: str) -> str:
    client_id, _, redirect_uri = settings()
    args = {
        "response_type": "code", "client_id": client_id,
        "redirect_uri": redirect_uri, "scope": SCOPES,
        "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256", "prompt": "consent",
    }
    return AUTH_URL + "?" + urlencode(args)


def token_request(data: dict[str, str]) -> dict:
    client_id, client_secret, _ = settings()
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            response = client.post(TOKEN_URL, data=data,
                                   auth=(client_id, client_secret),
                                   headers={"Accept": "application/json"})
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OAuthProviderError("Railway token exchange failed") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str):
        raise OAuthProviderError("Railway response did not contain access token")
    if payload.get("token_type", "Bearer").lower() != "bearer":
        raise OAuthProviderError("Unexpected Railway token type")
    expires = payload.get("expires_in", 3600)
    if not isinstance(expires, int) or not 60 <= expires <= 86400:
        raise OAuthProviderError("Invalid provider token expiry")
    payload["expires_in"] = expires
    return payload


def exchange_code(code: str, verifier: str) -> dict:
    _, _, redirect_uri = settings()
    return token_request({"grant_type": "authorization_code",
                          "code": code, "redirect_uri": redirect_uri,
                          "code_verifier": verifier})


def refresh_token(refresh: str) -> dict:
    return token_request({"grant_type": "refresh_token", "refresh_token": refresh})


def profile(access_token: str) -> dict:
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            response = client.get(ME_URL,
                                  headers={"Authorization": "Bearer " + access_token,
                                           "Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OAuthProviderError("Railway identity validation failed") from exc
    if not isinstance(data, dict) or not isinstance(data.get("sub"), str) or not data["sub"]:
        raise OAuthProviderError("Missing Railway subject identifier")
    return data


def expiry(expires_in: int):
    return utcnow() + timedelta(seconds=expires_in)


def readiness() -> dict:
    try:
        settings()
        cipher()
    except OAuthConfigurationError:
        return {"configured": False, "connection": "disabled"}
    return {"configured": True, "connection": "authorization_ready"}
