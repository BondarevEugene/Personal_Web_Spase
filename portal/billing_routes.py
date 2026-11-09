"""Customer billing views: read-only catalog and explicitly pending invoices.

No checkout URL exists until a verified payment-provider integration is ready.
"""
from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from portal.billing import BillingRuleError, create_pending_invoice, current_entitlements
from portal.db import session_factory
from portal.models import BillingPlan, Invoice
from portal.routes import current_customer, form_page
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/account/billing", tags=["Customer Billing"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def billing_page(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        plans = db.scalars(
            select(BillingPlan).where(BillingPlan.is_public.is_(True))
            .order_by(BillingPlan.code.asc())
        ).all()
        invoices = db.scalars(
            select(Invoice).where(Invoice.org_id == user.org_id)
            .order_by(Invoice.created_at.desc()).limit(30)
        ).all()
        entitlements = current_entitlements(db, user.org_id)
        return form_page(
            request, "billing.html", user=user, plans=plans, invoices=invoices,
            entitlements=entitlements,
            request_id=secrets.token_urlsafe(32),
            created=request.query_params.get("created") == "1",
        )


@router.get("/entitlements")
def entitlements(request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        response = JSONResponse(current_entitlements(db, user.org_id))
        response.headers["Cache-Control"] = "no-store"
        return response


@router.get("/paid-access")
def paid_access(request: Request):
    """Demonstration of server-side entitlement enforcement; no paid product exposed."""
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        rights = current_entitlements(db, user.org_id)
        if not rights["paid_access"]:
            raise HTTPException(status_code=402, detail="Active, verified paid subscription required")
        response = JSONResponse({"ok": True, "plan": rights["plan"],
                                 "paid_until": rights["paid_until"]})
        response.headers["Cache-Control"] = "no-store"
        return response


@router.post("/invoices")
def request_invoice(
    request: Request,
    csrf_token: str = Form(""),
    plan_code: str = Form(""),
    request_id: str = Form(""),
):
    secure_request(request)
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        user = current_customer(request, db)
        if not user:
            return RedirectResponse("/account/login", status_code=303)
        if user.role != "owner":
            raise HTTPException(status_code=403, detail="Organization owner required")
        try:
            create_pending_invoice(db, user.org_id, plan_code, request_id)
            db.commit()
        except BillingRuleError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except IntegrityError:
            # Unique request index is the last line of defense on concurrent POSTs.
            db.rollback()
            duplicate = db.scalar(
                select(Invoice).where(Invoice.org_id == user.org_id,
                                      Invoice.idempotency_key == request_id)
            )
            if duplicate is None or duplicate.plan_code != plan_code:
                raise HTTPException(status_code=409, detail="Invoice request conflict")
        return RedirectResponse("/account/billing?created=1", status_code=303)
