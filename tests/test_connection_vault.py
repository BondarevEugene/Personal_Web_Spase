"""Secure Vault encryption and OAuth state replay protection."""
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from automation.connection_vault import VaultUnavailable, rotate, seal, unseal
from automation.oauth_state import consume_state, issue_state
from portal.db import Base

CUSTOMER = "00000000-0000-0000-0000-000000000001"
CONNECTION = "00000000-0000-0000-0000-000000000002"


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


def test_oauth_state_one_use_and_tenant_binding():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        nonce = issue_state(db, customer_id=CUSTOMER, connection_id=CONNECTION)
        assert consume_state(db, nonce=nonce, customer_id="other") is None
        assert consume_state(db, nonce=nonce, customer_id=CUSTOMER) == CONNECTION
        assert consume_state(db, nonce=nonce, customer_id=CUSTOMER) is None
        assert consume_state(db, nonce="not-a-state", customer_id=CUSTOMER) is None
