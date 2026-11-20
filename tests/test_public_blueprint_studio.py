"""Blueprint Studio: bounded public configuration and no-persistence contract."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_studio import (
    INTEGRATIONS,
    PRIORITIES,
    PROCESSES,
    SECTORS,
    TEAMS,
    make_blueprint,
)
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)
URL = "/demo/blueprint"


def payload(**changes):
    data = {
        "sector": "crm", "team": "growth",
        "process": "manual", "priority": "control",
    }
    data.update(changes)
    return data


def test_public_builder_has_accessible_fields_and_valid_paths():
    response = CLIENT.get(URL)
    assert response.status_code == 200
    html = response.text
    assert html.count("<h1>") == 1
    assert 'action="/demo/blueprint#blueprint-result"' in html
    assert 'method="post"' in html
    for group in ("sector", "team", "process", "priority", "integration"):
        assert f'name="{group}"' in html
    assert 'href="/studio#contact"' in html
    assert 'href="/demo"' in html
    assert "не сохраняется в базе данных" in html
    assert 'id="blueprint-result"' not in html
    assert len(SECTORS) == 3
    assert len(TEAMS) == 3
    assert len(PROCESSES) == 3
    assert len(PRIORITIES) == 3
    assert len(INTEGRATIONS) == 4


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation"])
def test_actual_blueprints_use_real_products_and_honest_limits(sector):
    result = CLIENT.post(URL, data=payload(sector=sector))
    assert result.status_code == 200, result.text[:300]
    assert result.headers["cache-control"] == "no-store"
    assert "noindex" in result.headers["x-robots-tag"]
    assert 'id="blueprint-result"' in result.text
    assert "Критерии приёмки" in result.text
    assert "Риски и ограничения" in result.text
    assert "Скопировать бриф" in result.text
    assert "не смета" in result.text
    assert 'id="blueprint-output"' in result.text
    brief = make_blueprint(**payload(sector=sector))
    assert brief.title in result.text
    assert len(brief.stages) >= 5
    assert len(brief.acceptance) >= 4
    assert len(brief.components) >= 4
    assert len(brief.risks) >= 2
    assert brief.lead_url.startswith("/studio?topic=")
    assert "#contact" in brief.lead_url
    for component in brief.components:
        assert component in result.text


def test_integration_specific_architecture_has_real_safety_requirements():
    brief = make_blueprint(
        **payload(process="legacy", team="enterprise"),
        integrations=("payments", "external"),
    )
    assert any("идемпотентность" in component for component in brief.components)
    assert any("sandbox" in component for component in brief.components)
    assert any("переноса" in stage for stage in brief.stages)
    assert any("аудит доступа" in component for component in brief.components)
    assert any("провайдера" in risk for risk in brief.risks)


@pytest.mark.parametrize("field,bad", [
    ("sector", "invalid"), ("team", "unknown"), ("process", "unknown"),
    ("priority", "unknown"),
])
def test_unapproved_choices_are_rejected_without_side_effects(field, bad):
    response = CLIENT.post(URL, data=payload(**{field: bad}))
    assert response.status_code == 422


def test_duplicate_unknown_and_too_many_integrations_are_rejected():
    for selections in (
        ("telegram", "telegram"),
        ("database", "invalid"),
        ("telegram", "database", "payments", "external", "telegram"),
    ):
        with pytest.raises(ValueError):
            make_blueprint(**payload(), integrations=selections)


def test_missing_fields_rejected_and_no_user_account_created():
    assert CLIENT.post(URL, data={"sector": "crm"}).status_code == 422
    assert CLIENT.get("/account/login").status_code == 200
    assert CLIENT.get(URL).headers.get("set-cookie") is None


def test_blueprint_payload_has_no_html_injection():
    response = CLIENT.post(URL, data=payload(sector="<script>alert(1)</script>"))
    assert response.status_code == 422
    assert "<script>alert(1)</script>" not in response.text
    assert "<script>alert(1)</script>" not in make_blueprint(
        **payload(), integrations=("database",),
    ).text


def test_experience_lab_and_public_sitemap_discover_blueprint(monkeypatch):
    lab = CLIENT.get("/demo")
    assert lab.status_code == 200
    assert 'href="/demo/blueprint"' in lab.text
    assert CLIENT.get("/demo/blueprint").status_code == 200
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    sitemap = CLIENT.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "<loc>https://omni.example.com/demo/blueprint</loc>" in sitemap.text


def test_static_assets_are_accessible_responsive_and_small():
    css = CLIENT.get("/studio-assets/blueprint_studio.css")
    js = CLIENT.get("/studio-assets/blueprint_studio.js")
    entry = CLIENT.get("/studio-assets/blueprint_entry.css")
    for item in (css, js, entry):
        assert item.status_code == 200
    assert "max-width:490px" in css.text
    assert "prefers-reduced-motion" in css.text
    assert "@media print" in css.text
    assert "navigator.clipboard" in js.text
    assert "fetch(" not in js.text
    assert "localStorage" not in js.text
    assert len(js.content) < 3000
    assert (ROOT / "omni_site/templates/blueprint_studio.html").exists()
