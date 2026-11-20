"""Public Experience Lab: grounded scenario walkthroughs without live integrations."""
from pathlib import Path

from fastapi.testclient import TestClient

from omni_site.solution_journeys import BY_SLUG, JOURNEYS
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_three_real_scenarios_and_guarded_claims():
    assert {item.slug for item in JOURNEYS} == {
        "crm", "telegram", "automation",
    }
    assert len(BY_SLUG) == len(JOURNEYS)
    for item in JOURNEYS:
        assert len(item.steps) == 5
        assert len(item.constraints) >= 2
        assert len(item.facts) >= 3
        assert {step.code for step in item.steps} == {
            "01", "02", "03", "04", "05",
        }
        assert {step.node_type for step in item.steps} <= {
            "input", "database", "workflow", "decision", "output",
        }
        assert item.product_url.startswith("/")
        assert item.case_url.startswith("/cases/")
        assert item.service_url.startswith("/services/")
        assert CLIENT.get(item.case_url).status_code == 200
        assert CLIENT.get(item.service_url).status_code == 200


def test_experience_lab_public_route_has_keyboard_accessible_scenario_ui():
    response = CLIENT.get("/demo")
    assert response.status_code == 200, response.text[:500]
    html = response.text
    assert html.count("<h1>") == 1
    assert 'name="description"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-pressed="true"' in html
    assert "ДЕМОНСТРАЦИОННАЯ МОДЕЛЬ" in html
    assert "Здесь не выполняются API-запросы" in html
    assert 'href="/studio#contact"' in html
    for scenario in JOURNEYS:
        assert f'data-demo-tab="{scenario.slug}"' in html
        assert f'data-demo-panel="{scenario.slug}"' in html
        assert f'href="{scenario.case_url}"' in html
        assert f'href="{scenario.product_url}"' in html
        for step in scenario.steps:
            assert f'data-step-title="{step.title}"' in html
            assert step.explanation in html


def test_deep_links_show_selected_scenario_and_unknown_slug_is_404():
    for journey in JOURNEYS:
        response = CLIENT.get("/demo/" + journey.slug)
        assert response.status_code == 200, journey.slug
        assert journey.title in response.text
        assert (
            f'data-demo-tab="{journey.slug}" aria-pressed="true"'
        ) in response.text
        assert (
            f'data-demo-panel="{journey.slug}"'
        ) in response.text
        assert journey.challenge in response.text
        assert journey.constraints[0] in response.text
    assert CLIENT.get("/demo/unknown").status_code == 404
    assert CLIENT.get("/demo/%3Cscript%3E").status_code == 404


def test_homepage_and_search_sitemap_link_experience_lab(monkeypatch):
    page = CLIENT.get("/")
    assert page.status_code == 200
    assert 'href="/demo"' in page.text
    assert "Показываем путь решения." in page.text
    for journey in JOURNEYS:
        assert f'href="/demo/{journey.slug}"' in page.text

    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    result = CLIENT.get("/sitemap.xml")
    assert result.status_code == 200
    assert "<loc>https://omni.example.com/demo</loc>" in result.text
    for journey in JOURNEYS:
        assert (
            f"<loc>https://omni.example.com/demo/{journey.slug}</loc>"
        ) in result.text
    assert "/account/" not in result.text
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert CLIENT.get("/sitemap.xml").status_code == 404


def test_demo_assets_are_small_static_and_responsive():
    css = CLIENT.get("/studio-assets/solution_demo.css")
    script = CLIENT.get("/studio-assets/solution_demo.js")
    homepage_css = CLIENT.get("/studio-assets/demo_home.css")
    assert css.status_code == 200
    assert script.status_code == 200
    assert homepage_css.status_code == 200
    assert "prefers-reduced-motion" in css.text
    assert "max-width:480px" in css.text
    assert "max-width:850px" in homepage_css.text
    assert "replaceState" in script.text
    assert 'setAttribute("aria-pressed"' in script.text
    assert "fetch(" not in script.text
    assert "localStorage" not in script.text
    assert "XMLHttpRequest" not in script.text
    assert len(script.content) < 10_000
    assert (ROOT / "omni_site/templates/solution_demo.html").is_file()
