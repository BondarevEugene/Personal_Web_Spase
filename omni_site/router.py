"""Public software studio pages. Mount via app.include_router(router)."""
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE = Path(__file__).resolve().parent
router = APIRouter(tags=["Studio Website"])
templates = Jinja2Templates(directory=str(BASE / "templates"))

@router.get('/studio', response_class=HTMLResponse, name='studio_home')
def studio_home(request: Request):
    """Render the public portfolio without touching internal portal pages."""
    return templates.TemplateResponse(request=request, name='studio.html', context={})
