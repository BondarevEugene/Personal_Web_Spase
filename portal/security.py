"""Argon2id password storage, opaque DB-backed sessions and CSRF helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import HTTPException, Request, Response

from portal.models import utcnow

_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
_DUMMY_HASH = _hasher.hash("unused-dummy-password-123456")
SESSION_COOKIE = "omni_portal_session"
CSRF_COOKIE = "omni_portal_csrf"
SESSION_LIFETIME = timedelta(hours=12)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "testserver"}


def hash_password(value: str) -> str:
    return _hasher.hash(value)


def password_matches(hashed: str | None, attempted: str) -> bool:
    try:
        return bool(_hasher.verify(hashed or _DUMMY_HASH, attempted))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_session():
    token = secrets.token_urlsafe(32)
    return token, token_hash(token), utcnow() + SESSION_LIFETIME


def secure_request(request: Request) -> bool:
    # Do not accept credentials over remote HTTP. Proxy TLS must be configured.
    if request.url.hostname not in LOCAL_HOSTS and request.url.scheme != "https":
        raise HTTPException(status_code=503, detail="HTTPS is required for customer accounts")
    return request.url.scheme == "https"


def set_auth_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=secure_request(request),
                        samesite="lax", path="/", max_age=int(SESSION_LIFETIME.total_seconds()))


def issue_csrf(response: Response, request: Request, token: str | None = None) -> str:
    secure = secure_request(request)
    token = token or secrets.token_urlsafe(32)
    response.set_cookie(CSRF_COOKIE, token, httponly=True, secure=secure,
                        samesite="lax", path="/", max_age=3600)
    return token


def verify_csrf(request: Request, supplied: str) -> None:
    cookie = request.cookies.get(CSRF_COOKIE, "")
    if not cookie or not supplied or not hmac.compare_digest(cookie, supplied):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
