"""Customer registration, login, private cabinet and settings.

No credentials, bank details, or payment claims are stored in browser storage.
"""
from __future__ import annotations

import os
import re
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, OperationalError

from portal.db import session_factory
from portal.models import (Customer, CustomerSettings, Invoice, Organization, PaymentRecord,
                           PortalSession, RegistrationEvent, Subscription, utcnow)
from portal.security import (CSRF_COOKIE, SESSION_COOKIE, hash_password, issue_csrf,
                             new_session, password_matches, secure_request,
                             set_auth_cookie, token_hash, verify_csrf, new_csrf_token)

router = APIRouter(prefix="/account", tags=["Customer Portal"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
_LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
_USERNAME = re.compile(r"^[a-z][a-z0-9._-]{3,29}$")
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s]{2,}$")
_TZ = re.compile(r"^[A-Za-z0-9_+/-]{1,64}$")


def form_page(request: Request, name: str, **context):
    token = new_csrf_token()
    response = templates.TemplateResponse(request=request, name=name,
                                          context={"csrf_token": token, **context})
    issue_csrf(response, request, token)
    response.headers["Cache-Control"] = "no-store"
    return response


def current_customer(request: Request, db):
    raw = request.cookies.get(SESSION_COOKIE, "")
    if len(raw) < 30 or len(raw) > 200:
        return None
    session = db.get(PortalSession, token_hash(raw))
    if not session or session.expires_at <= utcnow():
        return None
    user = db.get(Customer, session.customer_id)
    return user if user and user.is_active else None


def login_limited(key: str) -> bool:
    now = time.monotonic()
    if len(_LOGIN_ATTEMPTS) > 5000:
        _LOGIN_ATTEMPTS.clear()
    hits = _LOGIN_ATTEMPTS[key]
    while hits and now - hits[0] > 600:
        hits.popleft()
    return len(hits) >= 8


def unsuccessful_login(key: str):
    _LOGIN_ATTEMPTS[key].append(time.monotonic())


def create_login(request: Request, db, customer: Customer):
    raw, hashed, expires = new_session()
    db.add(PortalSession(token_hash=hashed, customer_id=customer.id, expires_at=expires))
    db.commit()
    response = RedirectResponse("/account", status_code=303)
    set_auth_cookie(response, request, raw)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    secure_request(request)
    return form_page(request, "auth.html", mode="register", error=None)


@router.post("/register")
def register(request: Request, csrf_token: str = Form(""), username: str = Form(""),
             display_name: str = Form(""), email: str = Form(""),
             organization: str = Form(""), password: str = Form(""),
             password_repeat: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    if os.getenv("OMNI_PORTAL_ALLOW_REGISTRATION", "1") != "1":
        raise HTTPException(403, detail="Registration is currently disabled")
    username = username.strip().lower()
    email = email.strip().lower()
    display_name = display_name.strip()
    organization = organization.strip()
    problem = None
    if not _USERNAME.fullmatch(username):
        problem = "Логин: от 4 до 30 символов, латинские буквы, цифры, точка, дефис или _."
    elif len(email) > 254 or not _EMAIL.fullmatch(email):
        problem = "Укажи корректный адрес электронной почты."
    elif not 2 <= len(display_name) <= 120 or not 2 <= len(organization) <= 160:
        problem = "Укажи имя и название организации (от 2 символов)."
    elif not 8 <= len(password) <= 128 or password != password_repeat:
        problem = "Пароль: от 8 символов (рекомендуем 12+). Повтор пароля должен совпадать."
    if problem:
        return form_page(request, "auth.html", mode="register", error=problem)

    with session_factory()() as db:
        # Unique constraints remain the final arbiter of concurrent registrations.
        if db.scalar(select(Customer.id).where(or_(Customer.email == email,
                                                    Customer.username == username))):
            return form_page(request, "auth.html", mode="register",
                             error="Такой логин или email уже используется.")
        try:
            org = Organization(name=organization)
            db.add(org)
            db.flush()
            user = Customer(org_id=org.id, email=email, username=username,
                            display_name=display_name, password_hash=hash_password(password),
                            role="owner", email_verified=False)
            db.add(user)
            db.flush()
            db.add(CustomerSettings(customer_id=user.id))
            db.add(RegistrationEvent(customer_id=user.id, org_id=org.id, source="studio"))
            db.add(Subscription(org_id=org.id, plan_code="free", status="active",
                                price_minor=0, currency="UAH"))
            db.commit()
        except IntegrityError:
            db.rollback()
            return form_page(request, "auth.html", mode="register",
                             error="Не удалось зарегистрировать аккаунт: логин или email уже занят.")
        return create_login(request, db, user)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    secure_request(request)
    return form_page(request, "auth.html", mode="login", error=None)


@router.post("/login")
def login(request: Request, csrf_token: str = Form(""), login: str = Form(""),
          password: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    name = login.strip().lower()[:254]
    ip = request.client.host if request.client else "unknown"
    key = f"{ip}:{name}"
    if login_limited(key):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    with session_factory()() as db:
        user = db.scalar(select(Customer).where(or_(Customer.email == name,
                                                    Customer.username == name)))
        if not password_matches(user.password_hash if user else None, password) or not (user and user.is_active):
            unsuccessful_login(key)
            return form_page(request, "auth.html", mode="login",
                             error="Неверный логин или пароль.")
        _LOGIN_ATTEMPTS.pop(key, None)
        return create_login(request, db, user)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def account(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        org = db.get(Organization, user.org_id)
        settings = db.get(CustomerSettings, user.id)
        subscription = db.scalar(select(Subscription)
                                  .where(Subscription.org_id == user.org_id)
                                  .order_by(Subscription.created_at.desc()))
        invoices = db.scalars(select(Invoice).where(Invoice.org_id == user.org_id)
                              .order_by(Invoice.created_at.desc()).limit(30)).all()
        payments = db.scalars(select(PaymentRecord).where(PaymentRecord.org_id == user.org_id)
                              .order_by(PaymentRecord.created_at.desc()).limit(30)).all()
        return form_page(request, "dashboard.html", user=user, org=org, settings=settings,
                         subscription=subscription, invoices=invoices, payments=payments,
                         success=request.query_params.get("updated") == "1")


@router.post("/settings")
def update_settings(request: Request, csrf_token: str = Form(""),
                    display_name: str = Form(""), language: str = Form("ru"),
                    timezone: str = Form("Europe/Kyiv"),
                    marketing_opt_in: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    if not 2 <= len(display_name.strip()) <= 120:
        raise HTTPException(422, detail="Invalid display name")
    if language not in {"uk", "ru", "en"} or not _TZ.fullmatch(timezone):
        raise HTTPException(422, detail="Invalid account preferences")
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        settings = db.get(CustomerSettings, user.id)
        if not settings:
            settings = CustomerSettings(customer_id=user.id)
            db.add(settings)
        user.display_name = display_name.strip()
        settings.language = language
        settings.timezone = timezone
        settings.marketing_opt_in = marketing_opt_in == "yes"
        db.commit()
    return RedirectResponse("/account?updated=1", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    raw = request.cookies.get(SESSION_COOKIE, "")
    if raw:
        with session_factory()() as db:
            session = db.get(PortalSession, token_hash(raw))
            if session:
                db.delete(session)
                db.commit()
    response = RedirectResponse("/account/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
