# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: System API
# FILE: api/system.py
# ==============================================================================
# AUTHOR:  Yevhenii Bondariev
# ARCHITECT:OpenAI GPT-5.5
# ------------------------------------------------------------------------------
#
# PURPOSE
# Базовые системные endpoint платформы.
# Это первый API-модуль платформы.
# Используется:
#
# • Swagger
# • Monitoring
# • Runtime
# • Kubernetes
# • Docker
# • Mobile App
# • Telegram Bots
# • Health Checks
# • CI/CD
#
# ------------------------------------------------------------------------------
#
# ВАЖНО
#
# Здесь НЕ должно быть:
#
# • SQL
# • Builder
# • CRM
# • Deployment
#
# Только системная информация.
#
# ==============================================================================

from datetime import datetime
import os
import platform
import socket

from fastapi import APIRouter
from api.contracts import *
from api.responses import ApiResponse
from api.schemas import HealthResponse
router = APIRouter(
    prefix=f"{API_PREFIX}{SYSTEM_PREFIX}",
    tags=[TAG_SYSTEM]
)

@router.get(
    "/health",
    summary="Health Check",
    description="Проверка доступности платформы.",
    response_model=HealthResponse
)
async def health():

    return HealthResponse(
        status="ONLINE",
        platform=PLATFORM_NAME,
        version=CURRENT_VERSION
    )

@router.get(

    "/version",
    summary="Platform Version",
    response_model=ApiResponse
)
async def version():
    return ApiResponse(
        message="Platform version.",
        data={
            "platform": PLATFORM_NAME,
            "api": API_VERSION,
            "version": CURRENT_VERSION
        }
    )
@router.get(
    "/status",
    summary="Runtime Status",
    response_model=ApiResponse
)
async def status():
    return ApiResponse(
        message="Runtime status.",
        data={
            "status": STATUS_RUNNING,
            "server_time": datetime.utcnow(),
            "hostname": socket.gethostname()
        }
    )

@router.get(
    "/info",
    summary="Platform Information",
    response_model=ApiResponse
)
async def info():
    return ApiResponse(
        message="Platform information.",
        data={
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "system": platform.system(),
            "release": platform.release()
        }
    )

@router.get(
    "/environment",
    summary="Environment",
    response_model=ApiResponse
)
async def environment():
    return ApiResponse(
        message="Environment variables.",
        data={
            "cwd": os.getcwd(),
            "python_home": os.environ.get("PYTHONHOME"),
            "user": os.environ.get("USERNAME"),
            "computer": os.environ.get("COMPUTERNAME")
        }
    )

@router.get(
    "/ping",
    summary="Ping",
    response_model=ApiResponse
)
async def ping():
    return ApiResponse(
        message="pong"
    )

@router.get(
    "/license",
    summary="License",
    response_model=ApiResponse
)
async def license_info():
    return ApiResponse(
        message="License information.",
        data={
            "type": "Enterprise",
            "platform": PLATFORM_NAME,
            "version": CURRENT_VERSION
        }
    )

@router.get(
    "/openapi",
    summary="OpenAPI Information",
    response_model=ApiResponse
)
async def openapi():
    return ApiResponse(
        message="OpenAPI",
        data={
            "title": OPENAPI_TITLE,
            "description": OPENAPI_DESCRIPTION,
            "version": CURRENT_VERSION
        }
    )

@router.get(
    "/ready",
    summary="Readiness Probe",
    response_model=ApiResponse
)
async def ready():
    return ApiResponse(
        message="Platform is ready.",
        data={
            "ready": True
        }
    )

@router.get(
    "/live",
    summary="Liveness Probe",
    response_model=ApiResponse
)
async def live():
    return ApiResponse(
        message="Platform is alive.",
        data={
            "alive": True
        }
    )
__all__ = [
    "router"
]
