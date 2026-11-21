"""Protected Growth CRM pipeline for explicitly allowlisted platform operators."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from portal.db import session_factory
from portal.models import GrowthLead, utcnow
from portal.routes import form_page
from portal.security import verify_csrf
from portal.support_admin import require_operator

router = APIRouter(prefix="/support/growth", tags=["Growth CRM"])
STATUSES = ("new", "review", "contacted", "qualified", "won", "lost")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def growth_inbox(request: Request, status: str = ""):
    with session_factory()() as db:
        operator = require_operator(request, db)
        rows = db.scalars(select(GrowthLead).order_by(GrowthLead.created_at.desc()).limit(250)).all()
        counts = dict(Counter(lead.status for lead in rows))
        sources = dict(Counter(lead.utm_source or "direct / unknown" for lead in rows))
        visible = [lead for lead in rows if lead.status == status] if status in STATUSES else rows
        response = form_page(request, "growth_inbox.html", user=operator, leads=visible,
                             counts=counts, sources=sources, statuses=STATUSES,
                             filter_status=status)
        response.headers["X-Robots-Tag"] = "noindex"
        response.headers["Cache-Control"] = "no-store"
        return response


@router.post("/{lead_id}/status")
def update_growth_status(request: Request, lead_id: str,
                         csrf_token: str = Form(""), status: str = Form("")):
    verify_csrf(request, csrf_token)
    if status not in STATUSES:
        raise HTTPException(422, "Invalid status")
    with session_factory()() as db:
        require_operator(request, db)
        lead = db.get(GrowthLead, lead_id)
        if lead is None:
            raise HTTPException(404, "Lead not found")
        lead.status = status
        lead.updated_at = utcnow()
        db.commit()
    return RedirectResponse("/support/growth", status_code=303)
