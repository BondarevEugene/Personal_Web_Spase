"""Release smoke checker contracts, without external network calls."""
import io
import json
from urllib.error import HTTPError, URLError

import pytest

from scripts import verify_platform_staging as smoke


class Response:
    status = 200

    def __init__(self, text):
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.text.encode()


def test_staging_url_rejects_production_and_insecure_origins():
    for url in (
        "https://omnifactory.up.railway.app",
        "http://staging.example.com",
        "https://user:password@staging.example.com",
        "https://staging.example.com/private",
        "https://staging.example.com/?token=secret",
    ):
        with pytest.raises(ValueError):
            smoke.validate_url(url)
    assert smoke.validate_url("https://preview.example.com") == (
        "https://preview.example.com/"
    )
    assert smoke.validate_url("http://localhost:8765", allow_local=True).endswith(
        ":8765/"
    )


def test_health_requires_current_platform_identity(monkeypatch):
    monkeypatch.setattr(smoke, "urlopen", lambda *_a, **_k: Response(
        json.dumps({"status": "ok", "platform_ui": "studio-v3-platform"})
    ))
    result = smoke.check_endpoint("https://preview.example.com/", smoke.CHECKS[0])
    assert result["ok"] is True
    monkeypatch.setattr(smoke, "urlopen", lambda *_a, **_k: Response(
        json.dumps({"status": "ok", "platform_ui": "legacy"})
    ))
    assert smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )["ok"] is False


def test_home_rejects_legacy_page(monkeypatch):
    monkeypatch.setattr(smoke, "urlopen", lambda *_a, **_k: Response(
        "OMNIFACTORY MAIN_NODE BUILDER_PRO"
    ))
    assert smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[1]
    )["ok"] is False


def test_connection_errors_are_reported_without_credentials(monkeypatch):
    def offline(*_a, **_k):
        raise URLError("offline")

    monkeypatch.setattr(smoke, "urlopen", offline)
    result = smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )
    assert result == {"path": "/health", "ok": False, "error": "URLError"}


def test_expected_routes_cover_customer_builder_and_automation():
    paths = {check.path for check in smoke.CHECKS}
    assert {"/", "/health", "/account", "/architect",
            "/automation/studio", "/demo", "/services/ai-solutions"} <= paths
