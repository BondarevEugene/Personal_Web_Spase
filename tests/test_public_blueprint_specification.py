"""End-to-end technical specification export for all three Blueprint sectors."""
import re

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_specification import compile_specification
from server import app

CLIENT = TestClient(app)
URL = "/demo/blueprint/specification"
BASE = {"sector": "crm", "team": "growth", "process": "manual", "priority": "control"}


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation"])
def test_all_products_export_complete_downloadable_specification(sector):
    data = {**BASE, "sector": sector}
    response = CLIENT.post(URL, data=data)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-type"].startswith("text/markdown")
    assert re.fullmatch(
        r'attachment; filename="omnifactory-spec-[0-9a-f]{12}\.md"',
        response.headers["content-disposition"],
    )
    for number in range(1, 11):
        assert f"## {number}. " in response.text
    assert "не утверждённое ТЗ" in response.text
    assert response.text == compile_specification(**data).markdown


def test_integrations_are_order_independent_and_stable():
    a = compile_specification(
        **BASE, integrations=("payments", "telegram", "database"),
    )
    b = compile_specification(
        **BASE, integrations=("database", "payments", "telegram"),
    )
    assert a.revision == b.revision
    assert a.markdown == b.markdown
    assert "идемпотентность" in a.markdown


@pytest.mark.parametrize("field", ["sector", "team", "process", "priority"])
def test_invalid_fields_are_rejected(field):
    response = CLIENT.post(URL, data={**BASE, field: "<script>"})
    assert response.status_code == 422
    assert "<script>" not in response.text


def test_duplicate_and_unknown_integrations_are_rejected():
    for values in (["telegram", "telegram"], ["invalid"]):
        data = {**BASE, "integration": values}
        assert CLIENT.post(URL, data=data).status_code == 422


def test_missing_fields_and_get_are_not_accepted():
    assert CLIENT.post(URL, data={"sector": "crm"}).status_code == 422
    assert CLIENT.get(URL).status_code == 405


def test_public_form_exposes_real_download_without_js():
    html = CLIENT.post("/demo/blueprint", data=BASE).text
    assert 'form="blueprint-form"' in html
    assert 'formaction="/demo/blueprint/specification"' in html
    assert "Скачать техническое задание" in html
