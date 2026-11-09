# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Application Entry Point
# FILE: server.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# Главная точка входа платформы.
# ==============================================================================
#
# VERSION: 2.0.0
# ==============================================================================

from fastapi import FastAPI

from core.lifespan import lifespan
from core.middleware import setup_middleware
from core.static import mount_static

# ------------------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------------------
from routers.home import router as home_router
from routers.admin import router as admin_router

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from omni_site.router import router as studio_router
from omni_site.telegram_leads import router as studio_leads_router
from api.simple_builder import router as simple_builder_router
from portal.routes import router as customer_portal_router

# ------------------------------------------------------------------------------
# APP
# ------------------------------------------------------------------------------
app = FastAPI(
    title="OMNIFACTORY Platform",
    description="AI Development Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Infrastructure
# ------------------------------------------------------------------------------
setup_middleware(app)
mount_static(app)

# ------------------------------------------------------------------------------
# Include Routers
# ------------------------------------------------------------------------------
app.include_router(home_router)
app.include_router(admin_router)

# Публичный сайт студии OmniFactory
app.mount(
    "/studio-assets",
    StaticFiles(
        directory=str(
            Path(__file__).resolve().parent
            / "omni_site"
            / "static"
        )
    ),
    name="studio-assets",
)

app.include_router(studio_router)
app.include_router(studio_leads_router)
app.include_router(simple_builder_router)
app.include_router(customer_portal_router)

# ------------------------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "platform": "OMNIFACTORY",
        "version": "2.0.0",
        "platform_ui": "studio-v3-platform",
        "customer_portal": "accounts-v1"
    }