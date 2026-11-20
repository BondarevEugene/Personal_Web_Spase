"""AI Product Factory: deterministic, inspectable project discovery foundation.

No model API, code execution, credentials or deployment is triggered here.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from portal.db import session_factory
from portal.routes import current_customer
from portal.security import secure_request, verify_csrf
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


class BlueprintDecision(BaseModel):
    brief: ProductBrief
    blueprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted: bool
    acknowledged_open_questions: bool = False
    comment: str = Field(default="", max_length=1500)


def blueprint_digest(blueprint: dict) -> str:
    return hashlib.sha256(
        json.dumps(blueprint, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def decision_receipt(decision: BlueprintDecision, customer_id: str) -> dict:
    """Issue an auditable signed receipt, without claiming database persistence."""
    blueprint = build_blueprint(decision.brief)
    actual = blueprint_digest(blueprint)
    if actual != decision.blueprint_sha256:
        raise HTTPException(409, detail={
            "code": "BLUEPRINT_CHANGED",
            "message": "Техническое задание изменилось. Проверьте новую версию.",
            "current_sha256": actual,
        })
    if decision.accepted and blueprint["open_questions"] and not decision.acknowledged_open_questions:
        raise HTTPException(422, detail={
            "code": "UNRESOLVED_REQUIREMENTS",
            "message": "До утверждения ответьте на открытые вопросы.",
            "questions": blueprint["open_questions"],
        })
    return {
        "receipt_id": str(uuid4()),
        "customer_id": customer_id,
        "blueprint_sha256": actual,
        "brief_sha256": blueprint["brief_sha256"],
        "decision": "approved_with_open_questions" if decision.accepted and blueprint["open_questions"] else ("approved" if decision.accepted else "changes_requested"),
        "open_questions": blueprint["open_questions"],
        "comment": decision.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "automatic_implementation_started": False,
    }


@router.post("/review")
def review_blueprint(decision: BlueprintDecision, request: Request):
    """Authenticated review receipt, not a deployment or persistent approval."""
    secure_request(request)
    verify_csrf(request, request.headers.get("X-Omni-CSRF", ""))
    with session_factory()() as db:
        customer = current_customer(request, db)
        if customer is None:
            raise HTTPException(401, "Войдите в кабинет для согласования")
        receipt = decision_receipt(decision, str(customer.id))
    secret = os.environ.get("OMNI_PRODUCT_FACTORY_SIGNING_KEY")
    if not secret:
        raise HTTPException(503, "Подпись согласований не настроена")
    signed = URLSafeTimedSerializer(secret, salt="omni-product-factory-v1").dumps(receipt)
    return {"receipt": receipt, "signed_receipt": signed,
            "persistent_storage": False}


@router.get("/review/verify")
def verify_receipt(token: str, request: Request):
    """Verify signed review receipt with a 30-day expiry."""
    secure_request(request)
    with session_factory()() as db:
        customer = current_customer(request, db)
        if customer is None:
            raise HTTPException(401, "Войдите в кабинет")
        secret = os.environ.get("OMNI_PRODUCT_FACTORY_SIGNING_KEY")
        if not secret:
            raise HTTPException(503, "Подпись согласований не настроена")
        try:
            receipt = URLSafeTimedSerializer(
                secret, salt="omni-product-factory-v1"
            ).loads(token, max_age=30 * 86400)
        except BadSignature as exc:
            raise HTTPException(422, "Недействительная или просроченная подпись") from exc
        if receipt.get("customer_id") != str(customer.id):
            raise HTTPException(403, "Документ принадлежит другому аккаунту")
        return {"valid": True, "receipt": receipt}
