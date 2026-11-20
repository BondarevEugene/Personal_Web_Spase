"""Creative Content Studio: operator-only service and case editorial controls."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from omni_site.creative_store import catalog, publish, restore, save_draft, source
from portal.db import session_factory
from portal.models import PublicPageRevision
from portal.routes import form_page
from portal.security import verify_csrf
from portal.support_admin import require_operator

router = APIRouter(prefix="/support/creative", tags=["Creative Content Studio"])


def key_for(kind: str, slug: str) -> str:
    if kind not in {"service", "case"}:
        raise HTTPException(404, "Unknown content kind")
    key = kind + ":" + slug
    if source(key) is None:
        raise HTTPException(404, "Unknown content page")
    return key


def go(path: str):
    result = RedirectResponse(path, status_code=303)
    result.headers["Cache-Control"] = "no-store"
    return result


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def creative_dashboard(request: Request):
    with session_factory()() as db:
        operator = require_operator(request, db)
        pages = catalog()
        records = {key: db.get(PublicPageRevision, key) for key in pages}
        return form_page(
            request, "creative_studio_dashboard.html",
            user=operator, pages=pages, records=records,
        )


@router.get("/{kind}/{slug}", response_class=HTMLResponse)
def creative_editor(request: Request, kind: str, slug: str):
    key = key_for(kind, slug)
    with session_factory()() as db:
        operator = require_operator(request, db)
        page = source(key)
        record = db.get(PublicPageRevision, key)
        return form_page(
            request, "creative_studio_editor.html",
            user=operator, kind=kind, slug=slug, item=page, record=record,
            draft_title=record.draft_title if record else page.title,
            draft_summary=record.draft_summary if record else page.summary,
        )


@router.post("/{kind}/{slug}/save")
def save_page(request: Request, kind: str, slug: str,
              csrf_token: str = Form(""), title: str = Form(""),
              summary: str = Form("")):
    verify_csrf(request, csrf_token)
    key = key_for(kind, slug)
    with session_factory()() as db:
        operator = require_operator(request, db)
        try:
            save_draft(db, key, title, summary, operator.id)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        db.commit()
    return go("/support/creative/" + kind + "/" + slug)


@router.post("/{kind}/{slug}/publish")
def publish_page(request: Request, kind: str, slug: str,
                 csrf_token: str = Form(""),
                 scheduled_at: str = Form("")):
    verify_csrf(request, csrf_token)
    key = key_for(kind, slug)
    try:
        when = datetime.fromisoformat(scheduled_at) if scheduled_at else None
        if when is not None and (when.tzinfo is not None
                                 or when.year > 2100):
            raise ValueError("Use a naive UTC date/time before 2101")
    except ValueError as exc:
        raise HTTPException(422, "Schedule must be a UTC date and time") from exc
    with session_factory()() as db:
        operator = require_operator(request, db)
        try:
            publish(db, key, operator.id, at=when)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        db.commit()
    return go("/support/creative/" + kind + "/" + slug)


@router.post("/{kind}/{slug}/restore")
def restore_page(request: Request, kind: str, slug: str,
                 csrf_token: str = Form("")):
    verify_csrf(request, csrf_token)
    key = key_for(kind, slug)
    with session_factory()() as db:
        operator = require_operator(request, db)
        restore(db, key, operator.id)
        db.commit()
    return go("/support/creative/" + kind + "/" + slug)
