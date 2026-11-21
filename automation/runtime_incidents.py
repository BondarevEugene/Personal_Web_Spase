"""Deterministic incident triage for Railway deployments.

A provider SUCCESS is never evidence that the application or Telegram
delivery works. No remote restart or rollback is triggered by this module.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from automation.railway_reconciliation import classify


def diagnose(*, provider_status: str | None, checked_at: datetime | None,
             now: datetime, provider_error: bool = False,
             healthcheck_configured: bool | None = None,
             replicas: int | None = None) -> dict:
    state = classify(provider_status=provider_status, last_checked_at=checked_at,
                     now=now, inspection_failed=provider_error)
    code = state["state"]
    advice = {
        "provider_unavailable": ("RAILWAY_UNREACHABLE", "warning",
            "Проверьте Railway OAuth и повторите инспекцию"),
        "stale": ("STALE_OBSERVATION", "warning",
            "Обновите данные Railway перед принятием решения"),
        "provider_failure": ("DEPLOYMENT_FAILED", "critical",
            "Изучите логи Railway; не повторяйте запуск без выяснения причины"),
        "deploying": ("DEPLOYMENT_PENDING", "info",
            "Дождитесь завершения развёртывания и повторите проверку"),
        "deployed_unverified": ("APP_UNVERIFIED", "warning",
            "Проверьте /health приложения и отдельно доставку Telegram"),
        "not_deployed": ("NO_DEPLOYMENT", "warning",
            "Проверьте план и согласование перед первым запуском"),
        "unknown": ("UNKNOWN_PROVIDER_STATE", "warning",
            "Уточните статус в Railway и проверьте журнал развёртывания"),
    }
    incident_code, severity, next_action = advice[code]
    findings = []
    if code == "deployed_unverified" and healthcheck_configured is False:
        findings.append("Railway healthcheck не настроен")
    if replicas == 0 and code in {"deployed_unverified", "deploying"}:
        findings.append("Railway сообщает о нуле реплик")
    return {
        "incident_code": incident_code,
        "severity": severity,
        "provider_state": code,
        "provider_fresh": state["fresh"],
        "application_health": "not_verified",
        "telegram_delivery": "not_verified",
        "auto_recovery_permitted": False,
        "restart_performed": False,
        "rollback_performed": False,
        "findings": findings,
        "next_action": next_action,
    }


def timeline(samples: list[dict], *, now: datetime) -> list[dict]:
    """Summarize successive observations without inventing an outage duration."""
    result = []
    for sample in samples:
        report = diagnose(now=now, **sample)
        if result and result[-1]["incident_code"] == report["incident_code"]:
            result[-1]["observations"] += 1
        else:
            result.append({"incident_code": report["incident_code"],
                           "severity": report["severity"], "observations": 1,
                           "next_action": report["next_action"]})
    return result
