"""Protected growth lead inbox and conversion overview for platform operators."""

from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from portal.db import session_factory
from portal.models import GrowthLead, utcnow
from portal.security import verify_csrf
from portal.support_admin import require_operator

router = APIRouter(prefix="/support/growth", tags=["Growth CRM"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
STATUSES = ("new", "review", "contacted", "qualified", "won", "lost")


@router.get("", response_class=HTMLResponse)
def growth_inbox(request: Request, status: str = ""):
    with session_factory()() as db:
        operator = require_operator(request, db)
        leads = db.scalars(
            select(GrowthLead).order_by(GrowthLead.created_at.desc()).limit(250)
        ).all()
        counts = dict(Counter(lead.status for lead in leads))
        sources = dict(Counter(lead.utm_source or "direct / unknown" for lead in leads))
        visible = [lead for lead in leads if lead.status == status] if status in STATUSES else leads
        from portal.security import csrf_token
        return templates.TemplateResponse(
            request=request,
            name="growth_inbox.html",
            context={
                "operator": operator, "leads": visible,
                "counts": counts, "sources": sources,
                "statuses": STATUSES, "filter_status": status,
                "csrf_token": csrf_token(request),
            },
            headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"},
        )


@router.post("/{lead_id}/status")
def update_growth_status(
    request: Request,
    lead_id: str,
    csrf_token: str = Form(""),
    status: str = Form(""),
):
    verify_csrf(request, csrf_token)
    if status not in STATUSES:
        raise HTTPException(status_code=422, detail="Invalid status")
    with session_factory()() as db:
        require_operator(request, db)
        lead = db.get(GrowthLead, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead.status = status
        lead.updated_at = utcnow()
        db.commit()
    return RedirectResponse("/support/growth", status_code=303)
