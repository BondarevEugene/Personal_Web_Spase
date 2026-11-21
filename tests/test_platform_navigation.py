"""Public navigation and truthful operational page contracts."""
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_home_surfaces_all_supported_public_sections():
    page = client.get("/").text
    for link in ("/projects", "/robotization", "/techkillers", "/architect",
                 "/dashboard", "/studio", "/account", "/docs"):
        assert f'href="{link}"' in page, link
    assert "LEGACY TOOLS" not in page
    assert "Сохранили прежний интерфейс роботизации" not in page


def test_dashboard_uses_verified_endpoints_and_unified_navigation():
    response = client.get("/dashboard")
    assert response.status_code == 200
    page = response.text
    assert "/studio-assets/legacy_refresh.css?v=1" in page
    for endpoint in ("/health", "/api/v1/builder/simple/capabilities",
                     "/api/v1/builder/simple/integrations"):
        assert endpoint in page
    assert "2 RUNNING" not in page


def test_builder_legacy_links_share_current_editor():
    for url in ("/architect", "/builder", "/builder-pro",
                "/pages/builder_pro.html", "/pages/builder_pro_final.html"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert 'id="btn-new-scenario"' in response.text
        assert 'id="btn-cloud-save"' in response.text
        assert 'id="btn-test-canvas"' in response.text


def test_cloud_project_endpoints_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/builder/projects" in paths
    assert "/api/v1/builder/projects/{id}" in paths
    assert "/api/v1/builder/projects/csrf" in paths
