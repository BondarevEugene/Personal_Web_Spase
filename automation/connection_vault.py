"""Encrypted credential envelope for connector workers (never a public API).

Requires OMNI_CONNECTION_VAULT_KEYS: comma-separated Fernet keys, newest first.
Key rotation: prepend a new key; retain older keys until re-encryption.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

MAX_SECRET_BYTES = 8192


class VaultUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class SealedSecret:
    ciphertext: bytes
    key_version: int = 1


def _cipher() -> MultiFernet:
    raw = os.getenv("OMNI_CONNECTION_VAULT_KEYS", "")
    keys = [key.strip().encode("ascii") for key in raw.split(",") if key.strip()]
    if not keys:
        raise VaultUnavailable("Connection Vault keys are not configured")
    try:
        return MultiFernet([Fernet(key) for key in keys])
    except (ValueError, TypeError) as exc:
        raise VaultUnavailable("Invalid Connection Vault key configuration") from exc


def seal(secret: str) -> SealedSecret:
    value = secret.encode("utf-8")
    if not value or len(value) > MAX_SECRET_BYTES:
        raise ValueError("Credential length is invalid")
    return SealedSecret(ciphertext=_cipher().encrypt(value))


def unseal(ciphertext: bytes) -> str:
    try:
        return _cipher().decrypt(ciphertext).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise VaultUnavailable("Credential cannot be decrypted") from exc


def rotate(ciphertext: bytes) -> bytes:
    try:
        return _cipher().rotate(ciphertext)
    except InvalidToken as exc:
        raise VaultUnavailable("Credential cannot be rotated") from exc


def oauth_nonce() -> str:
    """Unpredictable OAuth state seed; bind to tenant and browser in DB."""
    return secrets.token_urlsafe(32)
