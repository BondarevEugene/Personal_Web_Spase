"""Safeguards for the platform-only operator service desk."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from portal import support_admin


def test_operator_access_denied_without_allowlist(monkeypatch):
    monkeypatch.delenv("OMNI_SUPPORT_OPERATOR_IDS", raising=False)
    monkeypatch.setattr(support_admin, "secure_request", lambda request: True)
    monkeypatch.setattr(
        support_admin, "current_customer",
        lambda request, db: SimpleNamespace(id="tenant-owner", role="owner"),
    )
    with pytest.raises(HTTPException) as error:
        support_admin.require_operator(None, object())
    assert error.value.status_code == 403


def test_operator_access_granted_by_exact_id_not_role(monkeypatch):
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", "staff-123")
    monkeypatch.setattr(support_admin, "secure_request", lambda request: True)
    monkeypatch.setattr(
        support_admin, "current_customer",
        lambda request, db: SimpleNamespace(id="staff-123", role="member"),
    )
    operator = support_admin.require_operator(None, object())
    assert operator.id == "staff-123"


def test_status_workflow_uses_whitelisted_transitions():
    assert "resolved" not in support_admin.ALLOWED_TRANSITIONS["new"]
    assert "in_progress" in support_admin.ALLOWED_TRANSITIONS["approved"]
    assert "review" in support_admin.ALLOWED_TRANSITIONS["closed"]
    assert "closed" not in support_admin.ALLOWED_TRANSITIONS["closed"]


def test_operator_routes_are_registered():
    paths = {
        (r.path, method)
        for r in support_admin.router.routes
        for method in getattr(r, "methods", set())
    }
    assert ("/support/desk", "GET") in paths
    assert ("/support/desk/{ticket_id}", "GET") in paths
    assert ("/support/desk/{ticket_id}/transition", "POST") in paths
    assert ("/support/desk/{ticket_id}/reply", "POST") in paths
