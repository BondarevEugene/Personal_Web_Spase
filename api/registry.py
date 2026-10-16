# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Registry API
# FILE: api/registry.py
# ==============================================================================
# AUTHOR:#     Yevhenii Bondariev
# ARCHITECT:#     OpenAI GPT-5.5
# ------------------------------------------------------------------------------
# PURPOSE
# Работа с Registry Builder.
#
# Registry является центральным каталогом модулей платформы.
#
# Используется:
#
# • Builder
# • Runtime
# • Compiler
# • Marketplace
# • AI
# • Deployment
#
# ------------------------------------------------------------------------------
# ВНИМАНИЕ
# Пока используются mock-данные.
# После подключения compiler.py и registry.json
# логика автоматически переключится на реальные данные.
# ==============================================================================

from datetime import datetime
from fastapi import APIRouter
from api.contracts import *
from api.responses import ApiResponse
from api.schemas import (ModuleSchema, RegistrySchema)
from pathlib import Path
import json

from services.module_manager import ModuleManager

manager = ModuleManager()

router = APIRouter(
    prefix=f"{API_PREFIX}{REGISTRY_PREFIX}",
    tags=[TAG_REGISTRY]
)

MOCK_MODULES = [
    ModuleSchema(
        id="telegram_sender",
        title="Telegram Sender",
        category="Communication",
        description="Send Telegram messages"
    ),

    ModuleSchema(
        id="crm_sync",
        title="CRM Synchronization",
        category="CRM",
        description="Synchronize CRM"
    ),

    ModuleSchema(
        id="ai_processor",
        title="AI Processor",
        category="Artificial Intelligence",
        description="LLM Processing"
    )

]


@router.get(
    "",
    summary="Registry",
    description="Полный реестр Builder.",
    response_model=ApiResponse
)
async def registry():
    registry = load_registry()
    return ApiResponse(
        message="Registry loaded.",
        data=registry
    )


@router.get(
    "/modules",
    summary="All Modules",
    response_model=ApiResponse
)
async def modules():
    registry = load_registry()
    return ApiResponse(
        message="Available modules.",
        data=registry
    )


@router.get(
    "/module/{module_id}",
    summary="Module Information",
    response_model=ApiResponse
)
async def module(module_id: str):
    registry = load_registry()
    for item in registry:
        if item.id == module_id:
            return ApiResponse(
                data=item
            )

    return ApiResponse(
        success=False,
        message="Module not found."
    )


async def categories():
    registry = load_registry()
    categories = sorted({
        module.category
        for module in registry

    })

    return ApiResponse(
        data=categories
    )


@router.get(
    "/search",
    summary="Search Modules",
    response_model=ApiResponse
)


async def search(query: str):
    registry = load_registry()
    result = [
        module
        for module in registry
        if query.lower() in module.title.lower()
    ]

    return ApiResponse(
        data=result
    )


@router.post(
    "/validate",
    summary="Validate Registry",
    response_model=ApiResponse
)
async def validate():
    registry = load_registry()
    return ApiResponse(
        message="Registry validated.",
        data={
            "valid": True,
            "checked": len(registry),
            "time": datetime.utcnow()
        }
    )


@router.post(
    "/reload",
    summary="Reload Registry",
    response_model=ApiResponse
)
async def reload_registry():
    return ApiResponse(
        message="Registry reloaded."
    )


@router.get(
    "/statistics",
    summary="Registry Statistics",
    response_model=ApiResponse
)
async def statistics():
    registry = load_registry()
    return ApiResponse(
        data={
            "modules": len(registry),
            "categories": len({
                m.category
                for m in registry
            }),
            "enabled": len(registry)
        }
    )


def load_registry():
    try:
        modules = manager.get_all_modules()
        if modules:
            result = []
            for item in modules:
                result.append(
                    ModuleSchema(
                        id=item.get("id", ""),
                        title=item.get("title", item.get("label", "")),
                        category=item.get("category", ""),
                        description=item.get("description", item.get("desc", ""))
                    )
                )
            return result
    except Exception as ex:
        print(ex)
    return MOCK_MODULES
