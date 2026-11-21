"""A zero-mutation release gate for customer-owned bot deployments.

Only operator-approved immutable OCI image digests are eligible. Neither
a customer-requested cap nor a review intent is a Railway cost quote or a
provider spending limit. No token is decrypted here or exported in a bundle.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

from automation.deployment import DeploymentSpec, build_plan

IMAGE = re.compile(
    r"^[a-z0-9][a-z0-9._/-]{2,180}@sha256:[0-9a-f]{64}$"
)
SUPPORTED_RUNTIMES = {"telegram_aiogram"}


def allowed_image(runtime: str) -> str | None:
    if runtime not in SUPPORTED_RUNTIMES:
        return None
    # Operator controls this mapping; it cannot be overridden in the user's
    # deployment plan or in a POST body.
    name = "OMNI_RELEASE_IMAGE_" + runtime.upper()
    value = os.getenv(name, "").strip()
    return value if IMAGE.fullmatch(value) else None


def scenario_sha256(scenario_json: str) -> str:
    parsed = json.loads(scenario_json)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def review_sha256(*, owner_id: str, bot_id: str, plan_id: str, plan_hash: str,
                  credential_fingerprint: str, revision_hash: str,
                  image: str, budget: int) -> str:
    payload = {
        "owner": owner_id, "bot": bot_id, "plan": plan_id,
        "manifest_sha256": plan_hash, "credential_fingerprint": credential_fingerprint,
        "scenario_sha256": revision_hash, "image": image, "budget_cap_usd": budget,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def checks(*, spec: DeploymentSpec, bot_owned: bool, token_verified: bool,
           image: str | None, binding_verified: bool, oauth_current: bool) -> list[dict]:
    return [
        {"code": "bot_ownership", "ok": bot_owned,
         "message": "Бот принадлежит текущему пользователю"},
        {"code": "runtime", "ok": spec.runtime == "telegram_aiogram",
         "message": "Поддерживается только проверенный Telegram runtime"},
        {"code": "token", "ok": token_verified,
         "message": "Telegram подтвердил сохранённый токен конкретного бота"},
        {"code": "image_digest", "ok": bool(image),
         "message": "Системный Docker-образ зафиксирован по sha256 и разрешён оператором"},
        {"code": "railway_binding", "ok": spec.mode == "byoc" and binding_verified,
         "message": "Выбран существующий, проверенный Railway-сервис (BYOC)"},
        {"code": "railway_oauth", "ok": spec.mode == "byoc" and oauth_current,
         "message": "Railway OAuth действителен для клиента"},
        {"code": "price_quote", "ok": False,
         "message": "Нет подтверждённой оценки стоимости и независимого лимита расходов"},
        {"code": "production_worker", "ok": False,
         "message": "Рабочий деплой, сверка ресурсов и безопасный откат пока отключены"},
        {"code": "runtime_health", "ok": False,
         "message": "Telegram webhook и /health ещё не проверены после публикации"},
    ]


def release_preview(*, spec: DeploymentSpec, bot_owned: bool,
                    token_verified: bool, binding_verified: bool,
                    oauth_current: bool) -> dict:
    image = allowed_image(spec.runtime)
    result = checks(spec=spec, bot_owned=bot_owned, token_verified=token_verified,
                    image=image, binding_verified=binding_verified,
                    oauth_current=oauth_current)
    return {
        "checks": result,
        "ready_for_review": all(v["ok"] for v in result if v["code"] in
            {"bot_ownership", "runtime", "token", "image_digest",
             "railway_binding", "railway_oauth"}),
        "ready_for_paid_deployment": False,
        "creates_resources": False,
        "estimated_cost_usd": None,
        "budget_cap_usd": spec.max_monthly_usd,
        "plan_sha256": build_plan(spec).manifest_sha256,
        "approved_image": image,
    }
