from datetime import timedelta
from types import SimpleNamespace

import pytest

from automation.provision_worker import recover_stale_jobs
from portal.models import utcnow


def test_recovery_rejects_invalid_limits():
    with pytest.raises(ValueError):
        recover_stale_jobs(timeout_minutes=0)
    with pytest.raises(ValueError):
        recover_stale_jobs(timeout_minutes=1441)
    with pytest.raises(ValueError):
        recover_stale_jobs(limit=0)
    with pytest.raises(ValueError):
        recover_stale_jobs(limit=1001)


def test_clock_is_naive_utc_for_provisioning_comparisons():
    now = utcnow()
    assert now.tzinfo is None
    assert now - timedelta(minutes=30) < now
