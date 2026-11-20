"""Public software studio pages. Mount via app.include_router(router)."""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG
from omni_site.content_store import public_articles, published_article
from portal.db import session_factory
from omni_site.case_library import CATEGORIES
from omni_site.creative_store import public_items, public_item
from omni_site.trust_content import PAGES, PAGE_BY_SLUG

BASE = Path(__file__).resolve().parent
router = APIRouter(tags=["Studio Website"])
templates = Jinja2Templates(directory=str(BASE / "templates"))

@router.get('/studio', response_class=HTMLResponse, name='studio_home')
def studio_home(request: Request):
    """Render the public portfolio without touching internal portal pages."""
    return templates.TemplateResponse(request=request, name='studio.html', context={})


@router.get("/journal", response_class=HTMLResponse, name="engineering_journal")
def engineering_journal(request: Request):
    """Static, source-grounded engineering journal with no customer claims."""
    with session_factory()() as db:
        articles = public_articles(db)
    return templates.TemplateResponse(
        request=request,
        name="engineering_journal.html",
        context={"articles": articles},
    )


@router.get("/journal/{slug}", response_class=HTMLResponse, name="engineering_article")
def engineering_article(request: Request, slug: str):
    if slug not in ARTICLE_BY_SLUG:
        raise HTTPException(status_code=404, detail="Article not found")
    with session_factory()() as db:
        article = published_article(db, slug)
        articles = public_articles(db)
    return templates.TemplateResponse(
        request=request,
        name="engineering_article.html",
        context={"article": article, "articles": articles},
    )


@router.get("/cases", response_class=HTMLResponse, name="public_case_library")
def public_case_library(request: Request):
    with session_factory()() as db:
        cases = public_items(db, "cases")
    return templates.TemplateResponse(
        request=request, name="case_library.html",
        context={"cases": cases, "categories": CATEGORIES},
    )


@router.get("/cases/{slug}", response_class=HTMLResponse, name="public_case_detail")
def public_case_detail(request: Request, slug: str):
    with session_factory()() as db:
        item = public_item(db, "cases", slug)
        cases = public_items(db, "cases")
    if item is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return templates.TemplateResponse(
        request=request, name="case_detail.html",
        context={"item": item, "cases": cases},
    )


@router.get("/services", response_class=HTMLResponse, name="services_directory")
def services_directory(request: Request):
    """Real public service directory; no production or ROI promises."""
    with session_factory()() as db:
        services = public_items(db, "services")
    return templates.TemplateResponse(
        request=request, name="service_directory.html",
        context={"services": services},
    )


@router.get("/services/{slug}", response_class=HTMLResponse, name="service_detail")
def service_detail(request: Request, slug: str):
    with session_factory()() as db:
        service = public_item(db, "services", slug)
        services = public_items(db, "services")
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return templates.TemplateResponse(
        request=request, name="service_detail.html",
        context={"service": service, "services": services},
    )


@router.get("/trust", response_class=HTMLResponse, name="public_trust_center")
def public_trust_center(request: Request):
    """Public evidence-based transparency and project onboarding."""
    return templates.TemplateResponse(
        request=request, name="trust_center.html",
        context={"pages": PAGES},
    )


@router.get("/trust/{slug}", response_class=HTMLResponse, name="public_trust_detail")
def public_trust_detail(request: Request, slug: str):
    page = PAGE_BY_SLUG.get(slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Trust topic not found")
    return templates.TemplateResponse(
        request=request, name="trust_detail.html",
        context={"page": page, "pages": PAGES},
    )
