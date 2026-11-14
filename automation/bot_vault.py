"""Tenant-bound Telegram token vault and fixed-destination BotFather token check.

Secrets are never returned to clients; only a privileged future deployment
worker may resolve credentials after checking the resource owner.
"""
from __future__ import annotations

import binascii
import hashlib
import os
import re

import httpx
from cryptography.fernet import Fernet, InvalidToken

TELEGRAM_TOKEN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{30,100}$")


class BotVaultUnavailable(RuntimeError):
    pass


class TelegramVerificationError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = os.getenv("OMNI_BOT_VAULT_FERNET_KEY", "")
    if not key:
        raise BotVaultUnavailable("Dedicated Bot Vault key is not configured")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise BotVaultUnavailable("Invalid Bot Vault encryption key") from exc


def encrypt_token(owner_id: str, project_id: str, token: str) -> tuple[str, str]:
    if not isinstance(token, str) or not TELEGRAM_TOKEN.fullmatch(token):
        raise ValueError("Invalid Telegram BotFather token format")
    fernet = _fernet()
    # Including the tenant/resource IDs prevents accidental ciphertext swapping.
    payload = f"{owner_id}:{project_id}:{token}"
    encrypted = fernet.encrypt(payload.encode()).decode("ascii")
    fingerprint = hashlib.sha256(encrypted.encode('ascii')).hexdigest()
    return encrypted, fingerprint


def decrypt_token(owner_id: str, project_id: str, encrypted: str) -> str:
    try:
        raw = _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise BotVaultUnavailable("Credential cannot be decrypted") from exc
    prefix = f"{owner_id}:{project_id}:"
    if not raw.startswith(prefix):
        raise BotVaultUnavailable("Credential owner or project mismatch")
    token = raw[len(prefix):]
    if not TELEGRAM_TOKEN.fullmatch(token):
        raise BotVaultUnavailable("Credential has invalid format")
    return token


def telegram_get_me(token: str) -> dict:
    """Explicit operator-requested verification; never interpolate untrusted host."""
    if not TELEGRAM_TOKEN.fullmatch(token):
        raise TelegramVerificationError("Invalid Telegram token format")
    # Telegram Bot API uses a bot token in its fixed URL path.
    # Proxy/access logs must redact /bot<token>/ paths.
    url = "https://api.telegram.org/bot" + token + "/getMe"
    try:
        with httpx.Client(timeout=8, follow_redirects=False, trust_env=False) as client:
            response = client.get(url)
            if len(response.content) > 16_384 or response.status_code != 200:
                raise TelegramVerificationError("Telegram token could not be verified")
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # Do not expose exception text: httpx RequestError may include token URL.
        raise TelegramVerificationError("Telegram verification unavailable") from exc
    if not isinstance(data, dict) or data.get("ok") is not True:
        raise TelegramVerificationError("Telegram rejected this token")
    result = data.get("result")
    if not isinstance(result, dict) or result.get("is_bot") is not True:
        raise TelegramVerificationError("Telegram did not return a bot identity")
    bot_id, username = result.get("id"), result.get("username")
    if not isinstance(bot_id, int) or not isinstance(username, str) or not re.fullmatch(
        r"[A-Za-z0-9_]{5,64}", username
    ):
        raise TelegramVerificationError("Invalid Telegram identity")
    return {"bot_id": str(bot_id), "username": username}


def readiness() -> bool:
    try:
        _fernet()
        return True
    except BotVaultUnavailable:
        return False
