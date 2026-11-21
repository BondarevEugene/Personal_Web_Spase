"""Product Factory review receipts and version-safe approval."""
import pytest
from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer

from api.product_factory import (
    BlueprintDecision,
    ProductBrief,
    blueprint_digest,
    build_blueprint,
    decision_receipt,
)


def sample():
    return ProductBrief(
        business="Ресторанная сеть с доставкой в городе",
        problem="Заявки из мессенджеров теряются между сотрудниками",
        users="Операторы и покупатели",
        outcome="Уменьшить время обработки заявок",
        kind="crm",
    )


def decision(**changes):
    brief = sample()
    data = {
        "brief": brief,
        "blueprint_sha256": blueprint_digest(build_blueprint(brief)),
        "accepted": False,
    }
    return BlueprintDecision.model_validate({**data, **changes})


def test_change_request_receipt_is_not_deployment():
    receipt = decision_receipt(decision(comment="Нужна роль менеджера"), "customer-1")
    assert receipt["decision"] == "changes_requested"
    assert receipt["automatic_implementation_started"] is False
    assert receipt["comment"] == "Нужна роль менеджера"


def test_stale_blueprint_cannot_be_approved():
    with pytest.raises(HTTPException) as exc:
        decision_receipt(decision(blueprint_sha256="0" * 64), "customer-1")
    assert exc.value.status_code == 409


def test_approval_requires_explicit_question_acknowledgement():
    with pytest.raises(HTTPException) as exc:
        decision_receipt(decision(accepted=True), "customer-1")
    assert exc.value.status_code == 422
    receipt = decision_receipt(
        decision(accepted=True, acknowledged_open_questions=True), "customer-1"
    )
    assert receipt["decision"] == "approved_with_open_questions"
    assert receipt["open_questions"]


def test_signed_receipt_is_verifiable_and_tamper_evident():
    receipt = decision_receipt(decision(), "customer-1")
    signer = URLSafeTimedSerializer("test-secret", salt="omni-product-factory-v1")
    token = signer.dumps(receipt)
    assert signer.loads(token, max_age=30 * 86400) == receipt
