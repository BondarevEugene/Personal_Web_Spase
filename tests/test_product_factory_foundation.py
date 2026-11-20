"""Product Factory blueprint contract and privacy boundaries."""
from fastapi.testclient import TestClient

from api.product_factory import ProductBrief, build_blueprint
from server import app


def sample(**changes):
    data = {
        "business": "Сервис доставки для местных ресторанов",
        "problem": "Заказы теряются между несколькими каналами связи",
        "users": "Операторы и клиенты",
        "outcome": "Сократить время обработки каждого заказа",
        "kind": "crm",
        "integrations": ["Telegram"],
    }
    return {**data, **changes}


def test_blueprint_is_stable_and_reviewable():
    brief = ProductBrief.model_validate(sample())
    first = build_blueprint(brief)
    assert first == build_blueprint(brief)
    assert first["status"] == "draft_requires_review"
    assert "SQLAlchemy" in first["proposed_stack"]
    assert first["integrations_requested"] == ["Telegram"]
    assert not first["capabilities"]["llm_used"]
    assert not first["capabilities"]["live_deployment"]


def test_all_supported_product_kinds():
    for kind in ("crm", "telegram_bot", "web_portal", "automation"):
        report = build_blueprint(ProductBrief.model_validate(sample(kind=kind)))
        assert report["modules"]
        assert report["product_kind"] == kind


def test_rejects_invalid_and_duplicate_integrations():
    from pydantic import ValidationError

    for integrations in (["Telegram", "Telegram"], [""], ["x" * 121]):
        try:
            ProductBrief.model_validate(sample(integrations=integrations))
        except ValidationError:
            continue
        raise AssertionError("Invalid integration accepted")


def test_http_contract_and_no_automatic_execution():
    client = TestClient(app)
    response = client.post("/api/v1/product-factory/blueprint", json=sample())
    assert response.status_code == 200
    data = response.json()
    assert data["capabilities"]["automatic_code_generation"] is False
    assert data["open_questions"]
    assert client.get("/api/v1/product-factory/capabilities").json()["llm_used"] is False
    assert client.post("/api/v1/product-factory/blueprint", json=sample(kind="invalid")).status_code == 422
