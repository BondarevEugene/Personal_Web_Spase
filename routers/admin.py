# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Administration Router
# FILE: routers/admin.py
#
# PURPOSE
# ------------------------------------------------------------------------------
# Маршруты административного интерфейса.
#
# ВАЖНО:
# Этот Router НЕ содержит бизнес-логику.
# Он только отображает административные страницы.
#
# Бизнес-логика находится:
#
#   routers/api.py
#   routers/deployment.py
#   routers/monitoring.py
#   routers/dashboard.py
#
# ==============================================================================

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.templates import render

router = APIRouter(
    prefix="/admin",
    tags=["Administration"]
)

# ==============================================================================
# ADMIN HOME
# ==============================================================================

@router.get("/", response_class=HTMLResponse)
async def admin_home(request: Request):

    return render(
        request,
        "admin.html",
        title="OMNIFACTORY Admin"
    )


# ==============================================================================
# DASHBOARD
# ==============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    return render(
        request,
        "dashboard.html",
        title="Dashboard"
    )


# ==============================================================================
# PROJECTS
# ==============================================================================

@router.get("/projects", response_class=HTMLResponse)
async def projects(request: Request):

    return render(
        request,
        "projects.html",
        title="Projects"
    )


# ==============================================================================
# BUILDER
# ==============================================================================

@router.get("/builder", response_class=HTMLResponse)
async def builder(request: Request):

    return render(
        request,
        "builder_pro_final.html",
        title="Bot Builder"
    )


# ==============================================================================
# ROBOTIZATION
# ==============================================================================

@router.get("/robotization", response_class=HTMLResponse)
async def robotization(request: Request):

    return render(
        request,
        "robotization.html",
        title="Robotization"
    )


# ==============================================================================
# TECHKILLERS
# ==============================================================================

@router.get("/techkillers", response_class=HTMLResponse)
async def techkillers(request: Request):

    return render(
        request,
        "techkillers.html",
        title="Technology Stack"
    )