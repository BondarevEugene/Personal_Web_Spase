"""Regression coverage for the three migrated public portal pages."""
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

CASES = (
    ("/projects", "/pages/projects.html", "Платформа / ПРОЕКТЫ"),
    ("/robotization", "/pages/robotization.html", "OMNIFACTORY / AUTOMATION"),
    ("/techkillers", "/pages/techkillers.html", "ENGINEERING / PLATFORM CAPABILITIES"),
)


def test_old_routes_have_unified_page_and_navigation():
    for canonical, old, _ in CASES:
        for route in (canonical, old):
            response = client.get(route)
            assert response.status_code == 200, route
            page = response.text
            assert "/studio-assets/legacy_refresh.css?v=2" in page
            assert 'class="omni-top"' in page
            assert 'class="omni-footer"' in page
            for link in ("/", "/architect", "/projects", "/robotization",
                         "/techkillers", "/studio", "/dashboard"):
                assert f'href="{link}"' in page, (route, link)


def test_shared_assets_accessible():
    response = client.get("/studio-assets/legacy_refresh.css")
    assert response.status_code == 200
    assert ".omni-nav" in response.text
    assert ".omni-grid" in response.text


def test_projects_do_not_present_archived_numerology_as_active():
    response = client.get("/projects")
    assert "Food_Porn" in response.text
    assert "OmniFactory CRM" in response.text
    assert "Genesis HR" in response.text
    assert "ИССЛЕДОВАТЕЛЬСКИЙ / АРХИВ" in response.text
    assert "CORE ACTIVE" not in response.text
    assert "SYSTEM_PROJECTS_REGISTRY" not in response.text


def test_robotization_never_impersonates_live_docker_supervisor():
    response = client.get("/pages/robotization.html")
    for unsupported in ("2 RUNNING", "3.45 / 8.0 GB", "PANIC MODE",
                        "INFINITE", "togglePanic", "ISO/IEC 27001 Certified"):
        assert unsupported not in response.text
    assert "Автоматический деплой" in response.text
    assert "Graph Studio" in response.text


def test_tech_page_replaces_old_genesys_dossier():
    response = client.get("/pages/techkillers.html")
    assert "FastAPI" in response.text
    assert "aiogram 3" in response.text
    assert "Docker Engine API" not in response.text
    assert "SYSTEM DOSSIER" not in response.text
    assert "NumPy Tensor Engine" not in response.text

def test_black_edition_assets_and_mentor_footer():
    for asset in ("black_platform.css", "visual_graph.svg", "visual_food.svg",
                  "visual_crm.svg", "visual_portal.svg", "visual_automation.svg",
                  "visual_engineering.svg"):
        response = client.get("/studio-assets/" + asset)
        assert response.status_code == 200, asset
        assert response.content
        if asset.endswith(".svg"):
            assert b"<svg" in response.content

    for route in ("/", "/projects", "/robotization", "/techkillers",
                  "/dashboard", "/architect", "/studio"):
        response = client.get(route)
        assert response.status_code == 200, route
        assert "Ольга Волощенко" in response.text or "Ольге Волощенко" in response.text
        assert 'href="https://t.me/Voloshka0602"' in response.text
        assert "Бондарев" in response.text or "БОНДАРЕВ" in response.text

    for route in ("/", "/architect"):
        assert "/studio-assets/black_platform.css?v=2" in client.get(route).text

    assert 'href="/bots/lab"' in client.get("/").text
    assert 'href="/automation/studio"' in client.get("/robotization").text
