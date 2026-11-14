"""Public/platform routes and legacy URL compatibility."""
from pathlib import Path

from fastapi import APIRouter, Request
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


@router.get("/robotization", response_class=HTMLResponse)
@router.get("/pages/robotization.html", response_class=HTMLResponse)
async def robotization(request: Request):
    """Legacy operational overview, separate from the actual visual builder."""
    return render(request, "robotization.html")


@router.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    """Legacy admin page. Not production-safe until authentication is implemented."""
    return render(request, "admin.html")
