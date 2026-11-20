"""Blueprint UI offers real persistence only for Telegram scenarios."""
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)
URL = "/demo/blueprint"


def data(sector):
    return {"sector": sector, "team": "growth", "process": "manual",
            "priority": "control", "integration": "telegram"}


def test_telegram_result_has_save_action():
    response = client.post(URL, data=data("telegram"))
    assert response.status_code == 200
    assert 'id="blueprint-save"' in response.text
    assert 'id="blueprint-save-status"' in response.text


def test_other_products_do_not_claim_graph_studio_persistence():
    for sector in ("crm", "automation"):
        response = client.post(URL, data=data(sector))
        assert response.status_code == 200
        assert 'id="blueprint-save"' not in response.text


def test_public_page_does_not_offer_save_without_blueprint():
    response = client.get(URL)
    assert response.status_code == 200
    assert 'id="blueprint-save"' not in response.text
