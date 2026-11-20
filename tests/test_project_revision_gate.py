"""Regression coverage for customer revision-to-redelivery gate."""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from portal.client_projects import require_fresh_delivery_after_revision


class FakeDb:
    def __init__(self, revision=None, delivery=None):
        self.revision = revision
        self.delivery = delivery
        self.calls = 0

    def scalar(self, statement):
        self.calls += 1
        return self.revision if self.calls == 1 else self.delivery


def test_first_delivery_cycle_has_no_revision_gate():
    db = FakeDb()
    require_fresh_delivery_after_revision(db, "project")
    assert db.calls == 1


def test_repeat_review_requires_fresh_delivery():
    db = FakeDb(revision=SimpleNamespace(created_at=datetime(2026, 11, 20)))
    with pytest.raises(HTTPException) as error:
        require_fresh_delivery_after_revision(db, "project")
    assert error.value.status_code == 409
    assert db.calls == 2


def test_new_delivery_allows_repeat_review():
    db = FakeDb(
        revision=SimpleNamespace(created_at=datetime(2026, 11, 20)),
        delivery="new-document-id",
    )
    require_fresh_delivery_after_revision(db, "project")
    assert db.calls == 2


def test_operator_template_explains_revision_gate():
    from pathlib import Path

    html = (
        Path(__file__).resolve().parents[1]
        / "portal/templates/client_project_operator.html"
    ).read_text(encoding="utf-8")
    assert "Описание результата" in html
    assert "повторной приёмки" in html
