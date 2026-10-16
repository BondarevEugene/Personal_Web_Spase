from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from core.templates import render

router = APIRouter(tags=["Public"])

BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# HOME
# ==============================================================================

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    index_file = BASE_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return render(request, "index.html")


# ==============================================================================
# ADMIN
# ==============================================================================

@router.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):

    return render(request, "admin.html")


# ==============================================================================
# DASHBOARD
# ==============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    return render(request, "dashboard.html")


# ==============================================================================
# ARCHITECT
# ==============================================================================

@router.get("/architect", response_class=HTMLResponse)
async def architect(request: Request):

    return render(request, "robotization.html")


# ==============================================================================
# PROJECTS
# ==============================================================================

@router.get("/projects.html", response_class=HTMLResponse)
async def projects(request: Request):

    return render(request, "projects.html")


# ==============================================================================
# BUILDER
# ==============================================================================

@router.get("/builder_pro_final.html", response_class=HTMLResponse)
async def builder(request: Request):

    return render(request, "builder_pro_final.html")


# ==============================================================================
# TECHKILLERS
# ==============================================================================

@router.get("/techkillers.html", response_class=HTMLResponse)
async def techkillers(request: Request):

    return render(request, "techkillers.html")