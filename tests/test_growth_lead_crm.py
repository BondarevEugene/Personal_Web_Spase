"""Growth lead intake and attribution regression tests."""

import pytest
from pydantic import ValidationError

from omni_site.telegram_leads import StudioLead, format_telegram_message
from portal.growth_admin import STATUSES
from portal.models import GrowthLead


def test_lead_requires_explicit_consent_to_be_accepted():
    lead = StudioLead(
        name="Test Client", contact="client@example.com",
        topic="CRM", message="Need a customer portal",
    )
    assert lead.consent is False


def test_lead_attribution_has_bounded_fields():
    with pytest.raises(ValidationError):
        StudioLead(
            name="Test Client", contact="client@example.com",
            topic="CRM", message="Need a customer portal",
            consent=True, utm_source="x" * 81,
        )


def test_telegram_html_escapes_user_content_and_source():
    lead = StudioLead(
        name="<b>Customer</b>", contact="client@example.com",
        topic="CRM", message="Need a customer portal <script>alert(1)</script>",
        source_path="/studio", utm_source="organic", consent=True,
    )
    text = format_telegram_message(lead)
    assert "&lt;b&gt;Customer&lt;/b&gt;" in text
    assert "&lt;script&gt;" in text
    assert "<script>" not in text
    assert "organic" in text


def test_growth_model_is_isolated_from_tenant_customer_records():
    assert GrowthLead.__tablename__ == "portal_growth_leads"
    assert "org_id" not in GrowthLead.__table__.columns
    assert {"name", "contact", "topic", "status", "telegram_status"}.issubset(
        GrowthLead.__table__.columns.keys()
    )


def test_growth_statuses_have_a_conversion_outcome():
    assert "new" in STATUSES
    assert "won" in STATUSES
    assert "lost" in STATUSES
