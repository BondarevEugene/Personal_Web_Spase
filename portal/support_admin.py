"""Protected OmniFactory operator support desk.

A customer owning an organization is NOT a platform operator. Operators must be
explicitly allowlisted by immutable customer UUID in OMNI_SUPPORT_OPERATOR_IDS.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from portal.db import session_factory
from portal.models import Customer, Organization, SupportEvent, SupportMessage, SupportTicket, utcnow
from portal.routes import current_customer, form_page, _SUPPORT_STATUS
from portal.security import secure_request, verify_csrf

router = APIRouter(prefix="/support/desk", tags=["OmniFactory Operator Desk"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

ALLOWED_TRANSITIONS = {
    "new": {"review", "closed"},
    "review": {"approved", "waiting_customer", "closed"},
    "approved": {"in_progress", "closed"},
    "in_progress": {"waiting_customer", "resolved", "closed"},
    "waiting_customer": {"review", "in_progress", "closed"},
    "resolved": {"in_progress", "closed"},
    "closed": {"review"},
}


def operator_ids() -> set[str]:
    # No default administrator and no access granted by the tenant-owned role.
    return {
        part.strip().lower()
        for part in os.getenv("OMNI_SUPPORT_OPERATOR_IDS", "").split(",")
        if part.strip()
    }


def require_operator(request: Request, db) -> Customer:
    secure_request(request)
    user = current_customer(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to OmniFactory")
    if user.id.lower() not in operator_ids():
        raise HTTPException(status_code=403, detail="Operator access required")
    return user


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def queue(request: Request, status: str = ""):
    with session_factory()() as db:
        operator = require_operator(request, db)
        stmt = select(SupportTicket).order_by(
            SupportTicket.updated_at.desc()
        ).limit(200)
        if status and status in _SUPPORT_STATUS:
            stmt = stmt.where(SupportTicket.status == status)
        tickets = db.scalars(stmt).all()
        org_names = {
            o.id: o.name
            for o in db.scalars(select(Organization)).all()
            if o.id in {t.org_id for t in tickets}
        }
        return form_page(request, "support_operator_queue.html",
                         operator=operator, tickets=tickets,
                         org_names=org_names, statuses=_SUPPORT_STATUS,
                         filter_status=status)


@router.get("/{ticket_id}", response_class=HTMLResponse)
def operator_detail(request: Request, ticket_id: str):
    with session_factory()() as db:
        operator = require_operator(request, db)
        ticket = db.get(SupportTicket, ticket_id)
        if ticket is None:
            raise HTTPException(404, detail="Ticket not found")
        org = db.get(Organization, ticket.org_id)
        messages = db.scalars(select(SupportMessage)
                              .where(SupportMessage.ticket_id == ticket.id)
                              .order_by(SupportMessage.created_at.asc()).limit(200)).all()
        events = db.scalars(select(SupportEvent)
                            .where(SupportEvent.ticket_id == ticket.id)
                            .order_by(SupportEvent.created_at.asc()).limit(200)).all()
        operators = db.scalars(select(Customer).where(Customer.id.in_(operator_ids()))).all()
        return form_page(request, "support_operator_detail.html",
                         operator=operator, ticket=ticket, org=org,
                         statuses=_SUPPORT_STATUS,
                         allowed=sorted(ALLOWED_TRANSITIONS.get(ticket.status, set())),
                         messages=messages, events=events, operators=operators)


@router.post("/{ticket_id}/transition")
def transition(request: Request, ticket_id: str, csrf_token: str = Form(""),
               new_status: str = Form(""), comment: str = Form(""),
               assigned_to_id: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    comment = comment.strip()
    assigned_to_id = assigned_to_id.strip()
    if len(comment) > 2000:
        raise HTTPException(422, detail="Comment too long")
    if assigned_to_id and assigned_to_id.lower() not in operator_ids():
        raise HTTPException(422, detail="Invalid operator assignment")
    with session_factory()() as db:
        operator = require_operator(request, db)
        # Row locking also protects PostgreSQL; SQLite serializes its writes.
        ticket = db.scalar(select(SupportTicket).where(
            SupportTicket.id == ticket_id
        ).with_for_update())
        if ticket is None:
            raise HTTPException(404, detail="Ticket not found")
        if new_status not in ALLOWED_TRANSITIONS.get(ticket.status, set()):
            raise HTTPException(409, detail="Invalid status transition")
        previous = ticket.status
        ticket.status = new_status
        ticket.assigned_to_id = assigned_to_id or None
        ticket.updated_at = utcnow()
        db.add(SupportEvent(
            ticket_id=ticket.id, actor_id=operator.id,
            old_status=previous, new_status=new_status,
            comment=comment,
        ))
        if comment:
            db.add(SupportMessage(ticket_id=ticket.id,
                                  author_id=operator.id, body=comment))
        db.commit()
    return RedirectResponse("/support/desk/" + ticket_id, status_code=303)


@router.post("/{ticket_id}/reply")
def operator_reply(request: Request, ticket_id: str,
                   csrf_token: str = Form(""), body: str = Form("")):
    secure_request(request)
    verify_csrf(request, csrf_token)
    body = body.strip()
    if not 1 <= len(body) <= 3000:
        raise HTTPException(422, detail="Message must contain 1–3000 characters")
    with session_factory()() as db:
        operator = require_operator(request, db)
        ticket = db.get(SupportTicket, ticket_id)
        if ticket is None:
            raise HTTPException(404, detail="Ticket not found")
        db.add(SupportMessage(ticket_id=ticket.id, author_id=operator.id, body=body))
        ticket.updated_at = utcnow()
        db.commit()
    return RedirectResponse("/support/desk/" + ticket_id, status_code=303)
