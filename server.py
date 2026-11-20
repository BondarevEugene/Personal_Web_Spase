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
from omni_site.blueprint_export import router as blueprint_export_router
from omni_site.blueprint_projects import router as blueprint_projects_router
from omni_site.blueprint_handoff import router as blueprint_handoff_router
from omni_site.graph_project_view import router as graph_project_view_router
from omni_site.search_discovery import router as public_search_router
from omni_site.telegram_leads import router as studio_leads_router
from api.simple_builder import router as simple_builder_router
from api.builder_projects import router as builder_projects_router
from api.automation import router as automation_router, WEBHOOKS as automation_webhook_router
from api.cloud_deploy import router as cloud_deploy_router
from api.railway_connections import router as railway_connections_router
from api.bot_lab import router as bot_lab_router
from api.cloud_provision import router as provision_router
from api.railway_resources import router as railway_resources_router
from api.bot_security import router as bot_security_router
from api.cloud_releases import router as cloud_releases_router
from api.telegram_runtime import router as telegram_runtime_router
from api.graph_operations import router as graph_operations_router
from portal.routes import router as customer_portal_router
from portal.account_security import router as account_security_router
from portal.billing_routes import router as customer_billing_router
from portal.finance_center import router as customer_finance_router
from portal.support_admin import router as support_admin_router
from portal.public_content_admin import router as public_content_router
from portal.creative_studio_admin import router as creative_studio_router
from portal.client_projects import router as client_projects_router, operator_router as operator_projects_router
from portal.project_attachments import (customer_router as customer_attachments_router,
                                       operator_router as operator_attachments_router)
from portal.project_diff import router as project_diff_router
from portal.project_documents import (customer_router as project_documents_router,
                                      operator_router as project_documents_operator_router,
                                      inbox_router as customer_inbox_router)

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
app.include_router(blueprint_export_router)
app.include_router(blueprint_projects_router)
app.include_router(blueprint_handoff_router)
app.include_router(graph_project_view_router)
app.include_router(public_search_router)
app.include_router(studio_leads_router)
app.include_router(simple_builder_router)
app.include_router(builder_projects_router)
app.include_router(automation_router)
app.include_router(automation_webhook_router)
app.include_router(cloud_deploy_router)
app.include_router(railway_connections_router)
app.include_router(bot_lab_router)
app.include_router(provision_router)
app.include_router(railway_resources_router)
app.include_router(bot_security_router)
app.include_router(cloud_releases_router)
app.include_router(telegram_runtime_router)
app.include_router(graph_operations_router)
app.include_router(customer_portal_router)
app.include_router(account_security_router)
app.include_router(customer_billing_router)
app.include_router(customer_finance_router)
app.include_router(support_admin_router)
app.include_router(public_content_router)
app.include_router(creative_studio_router)
app.include_router(client_projects_router)
app.include_router(operator_projects_router)
app.include_router(project_documents_router)
app.include_router(project_diff_router)
app.include_router(project_documents_operator_router)
app.include_router(customer_inbox_router)
app.include_router(customer_attachments_router)
app.include_router(operator_attachments_router)

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