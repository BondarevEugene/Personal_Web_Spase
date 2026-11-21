"""Public software studio pages. Mount via app.include_router(router)."""
import os
from pathlib import Path

from omni_site.search_discovery import canonical_origin
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG
from omni_site.content_store import public_articles, published_article
from portal.db import session_factory
from omni_site.case_library import CATEGORIES
from omni_site.creative_store import public_items, public_item
from omni_site.trust_content import PAGES, PAGE_BY_SLUG
from omni_site.solution_journeys import JOURNEYS, BY_SLUG
from omni_site.blueprint_specification import compile_specification
from omni_site.blueprint_delivery import make_delivery_package
from omni_site.blueprint_studio import (
    INTEGRATIONS, PRIORITIES, PROCESSES, SECTORS, TEAMS, make_blueprint,
)

BASE = Path(__file__).resolve().parent
router = APIRouter(tags=["Studio Website"])
templates = Jinja2Templates(directory=str(BASE / "templates"))


def public_origin() -> str | None:
    """Configured canonical site origin; never trust a request Host header."""
    return canonical_origin(os.getenv("OMNI_PUBLIC_BASE_URL", ""))

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
        context={"article": article, "articles": articles, "seo_origin": public_origin()},
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
        context={"item": item, "cases": cases, "seo_origin": public_origin()},
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
        context={"service": service, "services": services, "seo_origin": public_origin()},
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


@router.get("/demo", response_class=HTMLResponse, name="interactive_solution_demo")
def interactive_solution_demo(request: Request):
    """Educational product visualization, not a live service execution."""
    return templates.TemplateResponse(
        request=request, name="solution_demo.html",
        context={"journeys": JOURNEYS},
    )



@router.get("/demo/blueprint", response_class=HTMLResponse,
            name="blueprint_studio")
def blueprint_studio(request: Request):
    """Public opt-in architectural questionnaire with no persistence."""
    return templates.TemplateResponse(
        request=request, name="blueprint_studio.html",
        context={
            "sectors": SECTORS, "teams": TEAMS, "processes": PROCESSES,
            "priorities": PRIORITIES, "integrations": INTEGRATIONS,
            "blueprint": None,
        },
    )


@router.post("/demo/blueprint", response_class=HTMLResponse,
             name="create_blueprint")
def create_blueprint(
    request: Request,
    sector: str = Form(..., max_length=20),
    team: str = Form(..., max_length=20),
    process: str = Form(..., max_length=20),
    priority: str = Form(..., max_length=20),
    integration: list[str] | None = Form(None),
):
    """Purely derive an outline from public option IDs; never store a brief."""
    try:
        blueprint = make_blueprint(
            sector=sector, team=team, process=process, priority=priority,
            integrations=tuple(integration or ()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    response = templates.TemplateResponse(
        request=request, name="blueprint_studio.html",
        context={
            "sectors": SECTORS, "teams": TEAMS, "processes": PROCESSES,
            "priorities": PRIORITIES, "integrations": INTEGRATIONS,
            "blueprint": blueprint,
        },
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response



@router.post("/demo/blueprint/specification", name="download_blueprint_specification")
def download_blueprint_specification(
    sector: str = Form(..., max_length=20),
    team: str = Form(..., max_length=20),
    process: str = Form(..., max_length=20),
    priority: str = Form(..., max_length=20),
    integration: list[str] | None = Form(None),
):
    """Download a deterministic Markdown technical draft; no server persistence."""
    try:
        spec = compile_specification(
            sector=sector, team=team, process=process, priority=priority,
            integrations=tuple(integration or ()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=spec.markdown,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="omnifactory-spec-{spec.revision}.md"'
            ),
            "Cache-Control": "no-store",
            "X-Robots-Tag": "noindex, nofollow",
            "X-Content-Type-Options": "nosniff",
        },
    )



@router.post("/demo/blueprint/package", name="download_blueprint_package")
def download_blueprint_package(
    sector: str = Form(..., max_length=20),
    team: str = Form(..., max_length=20),
    process: str = Form(..., max_length=20),
    priority: str = Form(..., max_length=20),
    integration: list[str] | None = Form(None),
):
    """Download a complete offline handoff package without persistence."""
    try:
        package = make_delivery_package(
            sector=sector, team=team, process=process, priority=priority,
            integrations=tuple(integration or ()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=package.content,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="omnifactory-blueprint-{package.revision}.zip"'
            ),
            "Cache-Control": "no-store",
            "X-Robots-Tag": "noindex, nofollow",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/demo/{slug}", response_class=HTMLResponse,
            name="interactive_solution_detail")
def interactive_solution_detail(request: Request, slug: str):
    journey = BY_SLUG.get(slug)
    if journey is None:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return templates.TemplateResponse(
        request=request, name="solution_demo.html",
        context={"journeys": JOURNEYS, "selected": journey},
    )
