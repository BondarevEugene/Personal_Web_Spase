"""Telegram lead intake for the public OmniFactory Studio website.

Purpose:
    Receive contact requests from /studio and forward them through Telegram's
    Bot API **on the server**, without exposing bot credentials in HTML/JS.

Installation:
    In server.py, after app is created:
        from omni_site.telegram_leads import router as studio_leads_router
        app.include_router(studio_leads_router)

Environment (required for actual Telegram delivery):
    OMNI_STUDIO_BOT_TOKEN: Telegram bot token from BotFather.
    OMNI_STUDIO_CHAT_ID:  numeric user/group chat ID where leads should arrive.

Security:
    Data length limits, Pydantic validation, HTML escaping, honeypot, and a
    lightweight per-IP cooldown. For public production deployments, add
    a shared (Redis) rate limiter and anti-abuse challenge at the edge.
"""

from __future__ import annotations

import asyncio
import html
import os
import time
from collections import defaultdict, deque
from typing import Deque

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/studio/api", tags=["Studio Leads"])

# Lightweight process-local throttle; no database, so no alteration of CRM data.
_RATE_SECONDS = 600.0
_RATE_MAX = 3
_CLIENT_HITS: dict[str, Deque[float]] = defaultdict(deque)
_RATE_LOCK = asyncio.Lock()


class StudioLead(BaseModel):
    """Untrusted browser input; field limits prevent oversized Telegram messages."""

    name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=4, max_length=200)
    topic: str = Field(min_length=2, max_length=160)
    message: str = Field(min_length=10, max_length=3000)
    website: str = Field(default="", max_length=200)

    @field_validator("name", "contact", "topic", "message")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        """Disallow blank or control-only input even when raw length is valid."""
        clean = value.strip()
        if not clean or "\x00" in clean:
            raise ValueError("Invalid field value")
        return clean


def format_telegram_message(lead: StudioLead) -> str:
    """Escape all user fields before using Telegram's HTML parse mode."""
    esc = lambda value: html.escape(value, quote=True)
    return (
        "<b>◈ OMNIFACTORY · NEW LEAD</b>\n\n"
        f"<b>Имя:</b> {esc(lead.name)}\n"
        f"<b>Контакт:</b> {esc(lead.contact)}\n"
        f"<b>Направление:</b> {esc(lead.topic)}\n\n"
        f"<b>Задача:</b>\n{esc(lead.message)}"
    )


async def _check_rate_limit(client: str) -> None:
    """Permit at most three requests per 10 minutes for a process-local IP."""
    now = time.monotonic()
    async with _RATE_LOCK:
        # Bound memory growth by discarding stale IP entries during checks.
        if len(_CLIENT_HITS) > 10_000:
            for key in list(_CLIENT_HITS):
                hits = _CLIENT_HITS[key]
                while hits and now - hits[0] > _RATE_SECONDS:
                    hits.popleft()
                if not hits:
                    del _CLIENT_HITS[key]
        hits = _CLIENT_HITS[client]
        while hits and now - hits[0] > _RATE_SECONDS:
            hits.popleft()
        if len(hits) >= _RATE_MAX:
            raise HTTPException(status_code=429, detail="Too many requests")
        hits.append(now)


@router.post("/lead")
async def create_lead(lead: StudioLead, request: Request) -> dict[str, bool]:
    """Deliver an enquiry, returning success ONLY after Telegram confirms it."""
    # Bots filling the hidden field receive a generic success with no outbound request.
    if lead.website:
        return {"ok": True}

    token = os.getenv("OMNI_STUDIO_BOT_TOKEN", "").strip()
    chat_id = os.getenv("OMNI_STUDIO_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise HTTPException(status_code=503, detail="Telegram lead delivery not configured")

    # request.client.host is a connection IP. Do not blindly trust X-Forwarded-For.
    client_ip = request.client.host if request.client else "unknown"
    await _check_rate_limit(client_ip)

    payload = {
        "chat_id": chat_id,
        "text": format_telegram_message(lead),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
            response.raise_for_status()
            delivered = response.json().get("ok") is True
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Telegram unavailable") from exc
    if not delivered:
        raise HTTPException(status_code=502, detail="Telegram rejected delivery")
    return {"ok": True}
