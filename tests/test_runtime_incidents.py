"""Runtime incident diagnostics must never fabricate application health."""
from datetime import datetime, timedelta

import pytest

from automation.runtime_incidents import diagnose, timeline


NOW = datetime(2026, 11, 21, 12, 0)


@pytest.mark.parametrize(("status", "code"), [
    ("SUCCESS", "APP_UNVERIFIED"),
    ("FAILED", "DEPLOYMENT_FAILED"),
    ("BUILDING", "DEPLOYMENT_PENDING"),
    ("NO_DEPLOYMENT", "NO_DEPLOYMENT"),
    ("mystery", "UNKNOWN_PROVIDER_STATE"),
])
def test_incident_state_is_grounded(status, code):
    report = diagnose(provider_status=status, checked_at=NOW, now=NOW)
    assert report["incident_code"] == code
    assert report["application_health"] == "not_verified"
    assert report["telegram_delivery"] == "not_verified"
    assert report["auto_recovery_permitted"] is False
    assert report["restart_performed"] is False
    assert report["rollback_performed"] is False


def test_provider_outage_overrides_success():
    report = diagnose(provider_status="SUCCESS", checked_at=NOW, now=NOW,
                      provider_error=True)
    assert report["incident_code"] == "RAILWAY_UNREACHABLE"


def test_stale_observation_does_not_claim_healthy():
    report = diagnose(provider_status="SUCCESS",
                      checked_at=NOW - timedelta(minutes=30), now=NOW)
    assert report["incident_code"] == "STALE_OBSERVATION"


def test_zero_replicas_and_missing_healthcheck():
    report = diagnose(provider_status="SUCCESS", checked_at=NOW, now=NOW,
                      replicas=0, healthcheck_configured=False)
    assert len(report["findings"]) == 2


def test_timeline_collapses_adjacent_identical_observations():
    samples = [
        {"provider_status": "FAILED", "checked_at": NOW},
        {"provider_status": "FAILED", "checked_at": NOW},
        {"provider_status": "SUCCESS", "checked_at": NOW},
    ]
    events = timeline(samples, now=NOW)
    assert len(events) == 2
    assert events[0]["observations"] == 2
    assert events[1]["incident_code"] == "APP_UNVERIFIED"
