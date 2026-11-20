from datetime import datetime, timedelta

import pytest

from automation.railway_reconciliation import classify, summarize


NOW = datetime(2026, 11, 20, 18, 0)


@pytest.mark.parametrize(("status", "state"), [
    ("SUCCESS", "deployed_unverified"),
    ("FAILED", "provider_failure"),
    ("CRASHED", "provider_failure"),
    ("BUILDING", "deploying"),
    ("NO_DEPLOYMENT", "not_deployed"),
    ("unexpected", "unknown"),
])
def test_recent_provider_status_classification(status, state):
    result = classify(provider_status=status, last_checked_at=NOW, now=NOW)
    assert result["state"] == state
    assert result["telegram_delivery_verified"] is False
    assert result["bot_online"] is None


def test_stale_status_does_not_claim_online():
    result = classify(provider_status="SUCCESS",
                      last_checked_at=NOW - timedelta(minutes=16), now=NOW)
    assert result["state"] == "stale"
    assert result["requires_attention"]


def test_provider_error_overrides_cached_success():
    result = classify(provider_status="SUCCESS", last_checked_at=NOW, now=NOW,
                      inspection_failed=True)
    assert result["state"] == "provider_unavailable"


def test_future_timestamp_is_not_fresh():
    result = classify(provider_status="SUCCESS",
                      last_checked_at=NOW + timedelta(minutes=1), now=NOW)
    assert result["state"] == "stale"


def test_fleet_summary():
    good = classify(provider_status="SUCCESS", last_checked_at=NOW, now=NOW)
    bad = classify(provider_status="FAILED", last_checked_at=NOW, now=NOW)
    result = summarize([good, bad])
    assert result["total"] == 2
    assert result["attention"] == 1
    assert result["counts"]["provider_failure"] == 1


def test_invalid_freshness_window():
    with pytest.raises(ValueError):
        classify(provider_status="SUCCESS", last_checked_at=NOW,
                 now=NOW, max_age_minutes=0)
