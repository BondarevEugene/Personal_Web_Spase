"""Client account security center: password rotation and session revocation.

Every operation requires a logged-in DB-backed session and CSRF. Passwords are
never stored in logs or exposed in responses. No email reset or MFA is claimed.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import delete, func, select

from portal.db import session_factory
from portal.models import CustomerSettings, PortalSession, utcnow
from portal.routes import current_customer, form_page
from portal.security import (
    SESSION_COOKIE, hash_password, new_session, password_matches,
    secure_request, set_auth_cookie, token_hash, verify_csrf,
)

router = APIRouter(prefix="/account/security", tags=["Client Account Security"])


def sessions_for_user(db, customer_id: str):
    return db.scalars(select(PortalSession).where(
        PortalSession.customer_id == customer_id,
        PortalSession.expires_at > utcnow(),
    ).order_by(PortalSession.created_at.desc()).limit(50)).all()


def security_page(request: Request, notice: str | None = None):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        sessions = sessions_for_user(db, user.id)
        current = token_hash(request.cookies.get(SESSION_COOKIE, ""))
        return form_page(
            request, "account_security.html",
            user=user, settings=db.get(CustomerSettings, user.id),
            sessions=sessions, current_session_hash=current,
            changed=notice == "password", revoked=notice == "sessions",
        )


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def show_security(request: Request):
    notice = request.query_params.get("updated")
    return security_page(request, notice)


@router.post("/password")
def change_password(
    request: Request,
    csrf_token: str = Form(""),
    current_password: str = Form(""),
    new_password: str = Form(""),
    repeat_password: str = Form(""),
):
    secure_request(request)
    verify_csrf(request, csrf_token)
    if not 12 <= len(new_password) <= 128 or new_password != repeat_password:
        raise HTTPException(422, "Новый пароль: 12–128 символов, повтор должен совпадать")
    if len(current_password) > 128:
        raise HTTPException(422, "Некорректный текущий пароль")
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        if not password_matches(user.password_hash, current_password):
            # Avoid rendering submitted passwords back into the page.
            raise HTTPException(403, "Текущий пароль указан неверно")
        if password_matches(user.password_hash, new_password):
            raise HTTPException(422, "Новый пароль должен отличаться от предыдущего")
        user.password_hash = hash_password(new_password)
        # Revoke every old token (including other devices) and establish a new
        # login bound to this same user. Never reuse an old token after rotation.
        db.execute(delete(PortalSession).where(PortalSession.customer_id == user.id))
        raw, hashed, expires = new_session()
        db.add(PortalSession(token_hash=hashed, customer_id=user.id, expires_at=expires))
        db.commit()
    response = RedirectResponse("/account/security?updated=password", status_code=303)
    set_auth_cookie(response, request, raw)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/revoke-others")
def revoke_other_sessions(request: Request, csrf_token: str = Form(""),
                          password: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        if not password_matches(user.password_hash, password):
            raise HTTPException(403, "Подтвердите действие текущим паролем")
        current = token_hash(request.cookies.get(SESSION_COOKIE, ""))
        db.execute(delete(PortalSession).where(
            PortalSession.customer_id == user.id,
            PortalSession.token_hash != current,
        ))
        db.commit()
    response = RedirectResponse("/account/security?updated=sessions", status_code=303)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/logout-all")
def logout_all_sessions(request: Request, csrf_token: str = Form(""),
                        password: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        if not password_matches(user.password_hash, password):
            raise HTTPException(403, "Подтвердите действие текущим паролем")
        db.execute(delete(PortalSession).where(PortalSession.customer_id == user.id))
        db.commit()
    response = RedirectResponse("/account/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return response
