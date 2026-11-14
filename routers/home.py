"""Public/platform routes and legacy URL compatibility."""
from pathlib import Path

from fastapi import APIRouter, Request
from portal.db import session_factory
from portal.routes import current_customer
from portal.security import secure_request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.templates import render

router = APIRouter(tags=["OmniFactory Platform"])
BASE_DIR = Path(__file__).resolve().parent.parent


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        response = FileResponse(index_file)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Omni-UI"] = "studio-v3-platform"
        return response
    return render(request, "index.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Truthful system dashboard; previous fragment was not a complete page."""
    return render(request, "platform_dashboard.html")


@router.get("/architect", response_class=HTMLResponse)
@router.get("/builder", response_class=HTMLResponse)
@router.get("/pages/builder_pro_final.html", response_class=HTMLResponse)
@router.get("/builder-pro", response_class=HTMLResponse)
@router.get("/builder_pro_final.html", response_class=HTMLResponse)
@router.get("/pages/builder_pro.html", response_class=HTMLResponse)
async def builder(request: Request):
    """One stable URL target for the existing builder, including legacy links."""
    return render(request, "builder_pro_final.html")


@router.get("/projects", response_class=HTMLResponse)
@router.get("/projects.html", response_class=HTMLResponse)
@router.get("/pages/projects.html", response_class=HTMLResponse)
async def projects(request: Request):
    return render(request, "projects.html")


@router.get("/techkillers", response_class=HTMLResponse)
@router.get("/techkillers.html", response_class=HTMLResponse)
@router.get("/pages/techkillers.html", response_class=HTMLResponse)
async def techkillers(request: Request):
    return render(request, "techkillers.html")


@router.get("/cloud/deploy", response_class=HTMLResponse)
async def cloud_deploy(request: Request):
    """Safe Managed Cloud plan preview, not a live deployment console."""
    return render(request, "cloud_deploy.html")


@router.get("/automation/studio", response_class=HTMLResponse)
async def automation_studio(request: Request):
    """Real workflow editor with explicit dry-run execution controls."""
    return render(request, "automation_studio.html")


@router.get("/robotization", response_class=HTMLResponse)
@router.get("/pages/robotization.html", response_class=HTMLResponse)
async def robotization(request: Request):
    """Current public overview; all actions lead to verified platform routes."""
    return render(request, "robotization.html")


@router.get("/bots/lab", response_class=HTMLResponse)
@router.get("/bot-lab", response_class=HTMLResponse)
async def bot_lab(request: Request):
    """Authenticated operations workspace, not simulated admin telemetry."""
    secure_request(request)
    with session_factory()() as db:
        if current_customer(request, db) is None:
            return RedirectResponse("/account/login", status_code=303)
    response = render(request, "bot_lab.html")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/admin", include_in_schema=False)
async def legacy_admin(request: Request):
    return RedirectResponse("/bots/lab", status_code=307)
