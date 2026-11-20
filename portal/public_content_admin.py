"""Operator-only journal editing and technical SEO readiness panel."""
from __future__ import annotations

import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from omni_site.content_store import (
    parse_sections, publish, published_article,
    restore_original, save_draft, section_json,
)
from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG
from omni_site.search_discovery import canonical_origin
from omni_site.search_metrics import (
    MAX_REPORT_BYTES, parse_page_csv, report_summary, store_metrics,
)
from portal.db import session_factory
from portal.models import PublicArticleRevision
from portal.routes import form_page
from portal.security import verify_csrf
from portal.support_admin import require_operator

router = APIRouter(prefix="/support/content", tags=["Platform Editorial Control"])


def redirect_to(path: str):
    response = RedirectResponse(path, status_code=303)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def content_dashboard(request: Request):
    with session_factory()() as db:
        operator = require_operator(request, db)
        records = {
            a.slug: db.get(PublicArticleRevision, a.slug)
            for a in ARTICLES
        }
        domain = canonical_origin(os.getenv("OMNI_PUBLIC_BASE_URL", ""))
        seo_checks = (
            ("Публичный HTTPS-домен", domain is not None),
            ("Статьи с исходным содержанием", len(ARTICLES) >= 3),
            ("Sitemap доступен после настройки домена", domain is not None),
        )
        return form_page(
            request, "public_content_dashboard.html",
            user=operator, articles=ARTICLES, revisions=records,
            seo_checks=seo_checks, domain=domain,
            search_stats=report_summary(db),
            disclaimer="Поисковые показы, клики и заявки здесь не измеряются. "
                       "Для них требуется отдельный источник аналитики.",
        )


@router.get("/{slug}", response_class=HTMLResponse)
def edit_article(request: Request, slug: str, preview: bool = False):
    original = ARTICLE_BY_SLUG.get(slug)
    if original is None:
        raise HTTPException(404, "Article not found")
    with session_factory()() as db:
        operator = require_operator(request, db)
        record = db.get(PublicArticleRevision, slug)
        draft_title = record.draft_title if record else original.title
        draft_excerpt = record.draft_excerpt if record else original.excerpt
        draft_sections = (
            parse_sections(record.draft_sections)
            if record else original.sections
        )
        current_public = published_article(db, slug)
        return form_page(
            request, "public_content_editor.html", user=operator,
            article=original, record=record, draft_title=draft_title,
            draft_excerpt=draft_excerpt, draft_sections=draft_sections,
            current_public=current_public, preview=preview,
        )


@router.post("/{slug}/save")
def save_article(
    request: Request, slug: str,
    csrf_token: str = Form(""),
    title: str = Form(""), excerpt: str = Form(""),
    heading: list[str] = Form(...), body: list[str] = Form(...),
):
    verify_csrf(request, csrf_token)
    if slug not in ARTICLE_BY_SLUG:
        raise HTTPException(404, "Article not found")
    if len(heading) != len(body) or not 2 <= len(heading) <= 8:
        raise HTTPException(422, "Invalid number of sections")
    from omni_site.editorial import Section

    try:
        sections = section_json(tuple(
            Section(heading=h, body=b) for h, b in zip(heading, body)
        ))
        with session_factory()() as db:
            operator = require_operator(request, db)
            save_draft(
                db, slug, title.strip(), excerpt.strip(), sections, operator.id,
            )
            db.commit()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return redirect_to("/support/content/" + slug + "?preview=true")


@router.post("/{slug}/publish")
def publish_article(request: Request, slug: str, csrf_token: str = Form("")):
    verify_csrf(request, csrf_token)
    if slug not in ARTICLE_BY_SLUG:
        raise HTTPException(404, "Article not found")
    with session_factory()() as db:
        operator = require_operator(request, db)
        try:
            publish(db, slug, operator.id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        db.commit()
    return redirect_to("/support/content/" + slug)


@router.post("/{slug}/restore")
def restore_article(request: Request, slug: str, csrf_token: str = Form("")):
    verify_csrf(request, csrf_token)
    if slug not in ARTICLE_BY_SLUG:
        raise HTTPException(404, "Article not found")
    with session_factory()() as db:
        require_operator(request, db)
        restore_original(db, slug)
        db.commit()
    return redirect_to("/support/content/" + slug)


@router.post("/search-console/import")
async def import_search_console(
    request: Request, csrf_token: str = Form(""),
    report_date: str = Form(""), report: UploadFile = File(...),
):
    verify_csrf(request, csrf_token)
    with session_factory()() as db:
        require_operator(request, db)
        data = await report.read(MAX_REPORT_BYTES + 1)
        try:
            values = parse_page_csv(
                data, os.getenv("OMNI_PUBLIC_BASE_URL", ""), report_date,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        store_metrics(db, values)
        db.commit()
    return redirect_to("/support/content")
