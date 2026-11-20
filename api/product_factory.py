"""AI Product Factory: deterministic, inspectable project discovery foundation.

No model API, code execution, credentials or deployment is triggered here.
"""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/product-factory", tags=["Product Factory"])
ProductKind = Literal["telegram_bot", "crm", "web_portal", "automation"]


class ProductBrief(BaseModel):
    business: str = Field(min_length=10, max_length=2000)
    problem: str = Field(min_length=15, max_length=3000)
    users: str = Field(min_length=3, max_length=1000)
    outcome: str = Field(min_length=10, max_length=1500)
    kind: ProductKind
    integrations: list[str] = Field(default_factory=list, max_length=12)
    constraints: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("integrations", "constraints")
    @classmethod
    def clean_items(cls, value: list[str]) -> list[str]:
        items = [item.strip() for item in value]
        if any(not item or len(item) > 120 for item in items):
            raise ValueError("Each entry must be 1–120 characters")
        if len(set(items)) != len(items):
            raise ValueError("Duplicate entries are not allowed")
        return items


MODULES = {
    "telegram_bot": ["Диалоговые сценарии", "Пользовательские состояния",
                     "Администрирование", "Экспорт aiogram"],
    "crm": ["Клиенты", "Сделки и процессы", "Роли и доступ",
            "Отчёты и аудит"],
    "web_portal": ["Личный кабинет", "Контент и страницы",
                   "Авторизация", "Администрирование"],
    "automation": ["Триггеры", "Действия", "Обработка ошибок",
                   "Журнал запусков"],
}
STACK = {
    "telegram_bot": ["Python", "aiogram 3", "SQLite / PostgreSQL"],
    "crm": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "Jinja2"],
    "web_portal": ["Python", "FastAPI", "Jinja2", "PostgreSQL"],
    "automation": ["Python", "FastAPI", "SQLAlchemy"],
}


def build_blueprint(brief: ProductBrief) -> dict:
    """Generate a stable editable specification, not fictional AI-generated code."""
    source = brief.model_dump(mode="json")
    digest = hashlib.sha256(
        json.dumps(source, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    questions = []
    if not brief.integrations:
        questions.append("Какие внешние сервисы необходимо подключить?")
    if not brief.constraints:
        questions.append("Есть ли требования по бюджету, срокам и размещению данных?")
    questions.extend([
        "Какие роли пользователей нужны и какие действия им разрешены?",
        "Какие данные персонального характера будут обрабатываться?",
        "По каким измеримым критериям заказчик примет результат?",
    ])
    return {
        "schema_version": "1.0",
        "brief_sha256": digest,
        "status": "draft_requires_review",
        "product_kind": brief.kind,
        "problem": brief.problem,
        "target_users": brief.users,
        "business_outcome": brief.outcome,
        "modules": MODULES[brief.kind],
        "proposed_stack": STACK[brief.kind],
        "integrations_requested": brief.integrations,
        "constraints": brief.constraints,
        "acceptance_criteria": [
            "Основной пользовательский путь проходит от начала до конца",
            "Критические ошибки и отказы обрабатываются явно",
            "Права доступа проверяются на сервере",
            "Есть воспроизводимые тесты ключевых сценариев",
        ],
        "open_questions": questions,
        "delivery_stages": [
            "Согласование требований",
            "Архитектура и модель данных",
            "Реализация MVP",
            "Автоматические и ручные тесты",
            "Приёмка и согласованный запуск",
        ],
        "capabilities": {
            "automatic_code_generation": False,
            "live_deployment": False,
            "pricing_estimate": False,
            "llm_used": False,
        },
    }


@router.get("/capabilities")
def capabilities():
    return {
        "brief_to_blueprint": True,
        "automatic_code_generation": False,
        "live_deployment": False,
        "llm_used": False,
        "supported_products": list(MODULES),
    }


@router.post("/blueprint")
def blueprint(brief: ProductBrief):
    return build_blueprint(brief)
