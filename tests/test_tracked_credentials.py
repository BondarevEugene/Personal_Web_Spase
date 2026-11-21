"""Credential scanner tests use fake metadata, never actual secrets."""
import json

from scripts.check_tracked_credentials import violations


def test_detects_service_account_by_shape_without_sensitive_output(tmp_path):
    fake = {
        "type": "service_account",
        "private_key": "not-a-real-key",
        "private_key_id": "fake",
        "client_email": "fake@example.invalid",
    }
    (tmp_path / "innocent.json").write_text(json.dumps(fake), encoding="utf-8")
    result = violations(tmp_path, ["innocent.json"])
    assert result == ["innocent.json: tracked service-account credential"]
    assert "not-a-real-key" not in str(result)


def test_detects_forbidden_filename_even_if_invalid_json(tmp_path):
    (tmp_path / "firebase-adminsdk-example.json").write_text("{}", encoding="utf-8")
    assert violations(tmp_path, ["firebase-adminsdk-example.json"])


def test_ignores_regular_json_and_untracked_files(tmp_path):
    (tmp_path / "config.json").write_text('{"type":"service_account"}', encoding="utf-8")
    (tmp_path / "private.json").write_text('{"private_key":"fake"}', encoding="utf-8")
    assert violations(tmp_path, ["config.json"]) == []


def test_no_secrets_tracked_in_repository():
    assert violations() == []
