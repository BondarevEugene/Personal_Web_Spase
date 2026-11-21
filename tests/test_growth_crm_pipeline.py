"""Growth CRM lead pipeline and public consent contracts."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from omni_site.telegram_leads import StudioLead, format_telegram_message
from portal.growth_admin import STATUSES
from portal.models import GrowthLead

ROOT = Path(__file__).resolve().parents[1]


def test_lead_consent_and_attribution_contract():
    lead = StudioLead(name="Test Client", contact="contact@example.com",
                      topic="CRM", message="Please build a tailored CRM",
                      consent=True, utm_source="newsletter",
                      utm_campaign="november")
    assert lead.consent is True
    assert lead.utm_source == "newsletter"
    assert lead.utm_campaign == "november"
    with pytest.raises(ValidationError):
        StudioLead(name="", contact="x", topic="", message="short")


def test_telegram_payload_escapes_untrusted_fields():
    lead = StudioLead(name="<b>John</b>", contact="mail@example.com",
                      topic="CRM", message="Build a CRM <script>alert(1)</script>")
    message = format_telegram_message(lead)
    assert "&lt;script&gt;" in message
    assert "<script>" not in message


def test_growth_model_and_statuses():
    assert GrowthLead.__tablename__ == "portal_growth_leads"
    assert set(STATUSES) == {"new", "review", "contacted", "qualified", "won", "lost"}


def test_public_form_and_operator_page_are_wired():
    page = (ROOT / "omni_site/templates/studio.html").read_text(encoding="utf-8")
    js = (ROOT / "omni_site/static/site.js").read_text(encoding="utf-8")
    operator = (ROOT / "portal/templates/growth_inbox.html").read_text(encoding="utf-8")
    assert 'name="consent"' in page
    assert "utm_source" in js and "data.consent === 'yes'" in js
    assert "csrf_token" in operator
    assert "lead.telegram_status" in operator
