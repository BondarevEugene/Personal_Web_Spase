"""Secure Vault encryption and OAuth state replay protection."""
import pytest
from cryptography.fernet import Fernet

from automation.connection_vault import VaultUnavailable, rotate, seal, unseal


def test_vault_encryption_and_rotation(monkeypatch):
    first = Fernet.generate_key().decode()
    second = Fernet.generate_key().decode()
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", first)
    ciphertext = seal("sensitive-test-token").ciphertext
    assert b"sensitive-test-token" not in ciphertext
    assert unseal(ciphertext) == "sensitive-test-token"
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", f"{second},{first}")
    rotated = rotate(ciphertext)
    assert unseal(rotated) == "sensitive-test-token"
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", second)
    assert unseal(rotated) == "sensitive-test-token"
    with pytest.raises(VaultUnavailable):
        unseal(ciphertext)


def test_vault_fails_closed(monkeypatch):
    monkeypatch.delenv("OMNI_CONNECTION_VAULT_KEYS", raising=False)
    with pytest.raises(VaultUnavailable):
        seal("not-stored")
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", "invalid")
    with pytest.raises(VaultUnavailable):
        seal("not-stored")
    with pytest.raises(ValueError):
        seal("")




def test_provider_authorization_requires_explicit_configuration(monkeypatch):
    from automation.oauth_providers import authorization_url, settings

    monkeypatch.delenv("OMNI_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OMNI_GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("OMNI_OAUTH_REDIRECT_URI", raising=False)
    with pytest.raises(RuntimeError, match="incomplete"):
        settings("google_docs")
    with pytest.raises(ValueError, match="Unsupported"):
        settings("unsupported_provider")
    monkeypatch.setenv("OMNI_GOOGLE_CLIENT_ID", "example-client")
    monkeypatch.setenv("OMNI_GOOGLE_CLIENT_SECRET", "example-secret")
    monkeypatch.setenv("OMNI_OAUTH_REDIRECT_URI", "https://example.org/oauth/callback")
    url = authorization_url("google_sheets", "nonce", "pkce-challenge")
    assert "code_challenge_method=S256" in url
    assert "pkce-challenge" in url
    assert "example-secret" not in url


def test_vault_rejects_oversized_secret(monkeypatch):
    monkeypatch.setenv("OMNI_CONNECTION_VAULT_KEYS", Fernet.generate_key().decode())
    with pytest.raises(ValueError, match="length"):
        seal("x" * 8193)
