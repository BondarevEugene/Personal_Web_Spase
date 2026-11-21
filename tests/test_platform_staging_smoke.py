"""Release smoke checker contracts, without external network calls."""
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


class Opener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def open(self, *_args, **_kwargs):
        if self.error:
            raise self.error
        return self.response


def fake_opener(monkeypatch, *, text="", error=None):
    monkeypatch.setattr(
        smoke, "build_opener", lambda *_args: Opener(Response(text), error)
    )


def test_staging_url_rejects_production_and_insecure_origins():
    for url in (
        "https://omnifactory.up.railway.app",
        "https://www.omnifactory.up.railway.app",
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
    fake_opener(
        monkeypatch,
        text=json.dumps({"status": "ok", "platform_ui": "studio-v3-platform"}),
    )
    assert smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )["ok"]
    fake_opener(
        monkeypatch,
        text=json.dumps({"status": "ok", "platform_ui": "legacy"}),
    )
    assert not smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )["ok"]


def test_home_rejects_legacy_page(monkeypatch):
    fake_opener(monkeypatch, text="OMNIFACTORY MAIN_NODE BUILDER_PRO")
    assert not smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[1]
    )["ok"]


def test_connection_errors_are_reported_without_credentials(monkeypatch):
    fake_opener(monkeypatch, error=URLError("offline"))
    result = smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )
    assert result == {"path": "/health", "ok": False, "error": "URLError"}


def test_login_redirect_is_not_followed(monkeypatch):
    fake_opener(
        monkeypatch,
        error=HTTPError(
            "https://preview.example.com/account", 303, "See Other",
            {"Location": "https://outside.example.com/"}, None,
        ),
    )
    result = smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[7]
    )
    assert result["ok"] and result["status"] == 303


def test_unexpected_redirect_fails(monkeypatch):
    fake_opener(
        monkeypatch,
        error=HTTPError(
            "https://preview.example.com/health", 302, "Found",
            {"Location": "https://outside.example.com/"}, None,
        ),
    )
    assert not smoke.check_endpoint(
        "https://preview.example.com/", smoke.CHECKS[0]
    )["ok"]


def test_expected_routes_cover_customer_builder_automation_and_assets():
    paths = {check.path for check in smoke.CHECKS}
    assert {
        "/", "/health", "/account", "/architect", "/automation/studio",
        "/demo", "/services/ai-solutions", "/studio-assets/site.css",
        "/studio-assets/solution_demo.js",
    } <= paths
