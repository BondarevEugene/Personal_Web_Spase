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
#
# Здесь НЕ должно быть:
#   • бизнес-логики
#   • SQLAlchemy
#   • HTML
#   • API
#   • Builder
#   • Telegram
#   • CRM
#
# Только сборка приложения.
#
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
app.include_router(admin_router)


# Пока подключаем только Home.
# Остальные будем добавлять после их очистки.

# from routers.admin import router as admin_router
# from routers.api import router as api_router
# from routers.builder import router as builder_router
# from routers.dashboard import router as dashboard_router
# from routers.monitoring import router as monitoring_router
# from routers.deployment import router as deployment_router
# from routers.websocket import router as websocket_router

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
# Routers
# ------------------------------------------------------------------------------

app.include_router(home_router)

# app.include_router(admin_router)
# app.include_router(api_router)
# app.include_router(builder_router)
# app.include_router(dashboard_router)
# app.include_router(monitoring_router)
# app.include_router(deployment_router)
# app.include_router(websocket_router)

# ------------------------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health():

    return {
        "status": "ok",
        "platform": "OMNIFACTORY",
        "version": "2.0.0"
    }