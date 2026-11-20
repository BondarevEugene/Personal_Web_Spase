"""Public software studio pages. Mount via app.include_router(router)."""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG
from omni_site.case_library import CASES, CASE_BY_SLUG, CATEGORIES
from omni_site.services_catalog import SERVICES, SERVICE_BY_SLUG

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
    return templates.TemplateResponse(
        request=request,
        name="engineering_journal.html",
        context={"articles": ARTICLES},
    )


@router.get("/journal/{slug}", response_class=HTMLResponse, name="engineering_article")
def engineering_article(request: Request, slug: str):
    article = ARTICLE_BY_SLUG.get(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse(
        request=request,
        name="engineering_article.html",
        context={"article": article, "articles": ARTICLES},
    )


@router.get("/cases", response_class=HTMLResponse, name="public_case_library")
def public_case_library(request: Request):
    return templates.TemplateResponse(
        request=request, name="case_library.html",
        context={"cases": CASES, "categories": CATEGORIES},
    )


@router.get("/cases/{slug}", response_class=HTMLResponse, name="public_case_detail")
def public_case_detail(request: Request, slug: str):
    item = CASE_BY_SLUG.get(slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return templates.TemplateResponse(
        request=request, name="case_detail.html",
        context={"item": item, "cases": CASES},
    )


@router.get("/services", response_class=HTMLResponse, name="services_directory")
def services_directory(request: Request):
    """Real public service directory; no production or ROI promises."""
    return templates.TemplateResponse(
        request=request, name="service_directory.html",
        context={"services": SERVICES},
    )


@router.get("/services/{slug}", response_class=HTMLResponse, name="service_detail")
def service_detail(request: Request, slug: str):
    service = SERVICE_BY_SLUG.get(slug)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return templates.TemplateResponse(
        request=request, name="service_detail.html",
        context={"service": service, "services": SERVICES},
    )
