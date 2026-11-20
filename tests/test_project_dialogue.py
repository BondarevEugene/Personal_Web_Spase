"""Project dialogue authorization and message boundaries."""
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from portal.project_dialogue import validate_message
from server import app


@pytest.mark.parametrize("body", ["", "short", " " * 20, "x" * 2001])
def test_reject_invalid_messages(body):
    with pytest.raises(HTTPException) as error:
        validate_message(body)
    assert error.value.status_code == 422


def test_normalize_message():
    assert validate_message("  This is a real update.  ") == "This is a real update."


def test_anonymous_post_cannot_send_message():
    response = TestClient(app).post(
        "/account/projects/00000000-0000-0000-0000-000000000001/messages",
        data={"body": "Please update the technical specification"},
        follow_redirects=False,
    )
    assert response.status_code in (403, 303)


def test_customer_and_operator_forms_present():
    root = Path(__file__).resolve().parents[1] / "portal/templates"
    for name in ("client_project_detail.html", "client_project_operator.html"):
        html = (root / name).read_text(encoding="utf-8")
        assert "/messages" in html
        assert 'name="csrf_token"' in html
        assert 'name="body"' in html
