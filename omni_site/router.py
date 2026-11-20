"""Public software studio pages. Mount via app.include_router(router)."""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG

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
