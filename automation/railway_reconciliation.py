"""Pure Railway fleet reconciliation with explicit non-health semantics.

Never equate a Railway deployment status with verified Telegram delivery.
"""
from __future__ import annotations

from datetime import datetime, timedelta

SUCCESS = {"SUCCESS"}
IN_PROGRESS = {"BUILDING", "DEPLOYING", "INITIALIZING", "QUEUED", "WAITING"}
FAILURE = {"FAILED", "CRASHED", "REMOVED", "CANCELED"}


def classify(*, provider_status: str | None, last_checked_at: datetime | None,
             now: datetime, max_age_minutes: int = 15,
             inspection_failed: bool = False) -> dict:
    if not 1 <= max_age_minutes <= 1440:
        raise ValueError("Invalid freshness window")
    fresh = (last_checked_at is not None and
             timedelta(0) <= now - last_checked_at <=
             timedelta(minutes=max_age_minutes))
    status = (provider_status or "").upper()
    if inspection_failed:
        state = "provider_unavailable"
    elif not fresh:
        state = "stale"
    elif status in FAILURE:
        state = "provider_failure"
    elif status in IN_PROGRESS:
        state = "deploying"
    elif status in SUCCESS:
        state = "deployed_unverified"
    elif status == "NO_DEPLOYMENT":
        state = "not_deployed"
    else:
        state = "unknown"
    return {
        "state": state,
        "fresh": fresh and not inspection_failed,
        "provider_status": provider_status,
        "telegram_delivery_verified": False,
        "bot_online": None,
        "requires_attention": state in {
            "provider_unavailable", "stale", "provider_failure", "unknown",
        },
    }


def summarize(items: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for item in items:
        state = item["state"]
        counts[state] = counts.get(state, 0) + 1
    return {
        "total": len(items),
        "counts": counts,
        "attention": sum(bool(item["requires_attention"]) for item in items),
        "telegram_delivery_verified": False,
    }
