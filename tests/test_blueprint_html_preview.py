"""HTML preview is usable, read-only, escaped and consistent with JSON."""
import json

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_project_plan import build_project_plan
from omni_site.blueprint_specification import compile_specification
from server import app

CLIENT = TestClient(app)


def payload(sector="crm"):
    spec = compile_specification(
        sector=sector, team="growth", process="manual", priority="control",
    )
    plan = build_project_plan(spec)
    return {
        "schema": "omnifactory.blueprint.plan.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "architecture": plan.architecture,
        "milestones": plan.milestones,
        "verification": plan.verification,
        "risks": plan.risks,
    }


def upload(data):
    return CLIENT.post(
        "/demo/blueprint/preview/html",
        files={
            "plan_file": (
                "blueprint.json",
                json.dumps(data, ensure_ascii=False).encode("utf-8"),
                "application/json",
            )
        },
    )


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_html_preview_shows_full_plan_without_execution(sector):
    data = payload(sector)
    response = upload(data)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert "text/html" in response.headers["content-type"]
    html = response.text
    assert data["revision"] in html
    assert "Паспорт проекта" in html
    assert "Не импортировано" in html
    assert "Архитектура" in html
    assert "План реализации" in html
    assert "Критерии проверки" in html
    assert "Риски" in html
    for node in data["architecture"]["nodes"]:
        assert node["id"] in html
    assert "/studio-assets/blueprint_plan_preview.css" in html


def test_html_preview_escapes_untrusted_component_labels():
    data = payload()
    data["architecture"]["nodes"][0]["label"] = '<script>alert("x")</script>'
    response = upload(data)
    assert response.status_code == 200
    assert "&lt;script&gt;" in response.text
    assert '<script>alert("x")</script>' not in response.text


def test_html_preview_rejects_invalid_upload_and_is_not_gettable():
    response = CLIENT.post(
        "/demo/blueprint/preview/html",
        files={"plan_file": ("invalid.json", b"{}", "application/json")},
    )
    assert response.status_code == 422
    assert CLIENT.get("/demo/blueprint/preview/html").status_code == 405


def test_blueprint_form_opens_human_preview():
    response = CLIENT.get("/demo/blueprint")
    assert response.status_code == 200
    assert 'action="/demo/blueprint/preview/html"' in response.text
