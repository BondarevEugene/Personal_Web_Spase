"""Central middleware configuration for the OmniFactory web platform.

Credentialed CORS is intentionally opt-in.  The default same-origin frontend
does not need credentialed cross-origin requests.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


def cors_origins_from_env() -> list[str]:
    """Read explicit trusted origins; never combine wildcard with credentials."""
    configured = os.getenv("OMNIFACTORY_CORS_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in configured.split(",") if item.strip()]
    if "*" in origins:
        raise ValueError(
            "OMNIFACTORY_CORS_ORIGINS must contain explicit origins, not '*'. "
            "Omit the variable for same-origin operation."
        )
    if any(not origin.startswith(("http://", "https://")) for origin in origins):
        raise ValueError("OMNIFACTORY_CORS_ORIGINS requires http:// or https:// origins")
    return list(dict.fromkeys(origins))


def setup_middleware(app: FastAPI) -> None:
    """Configure compression and CORS once at app creation."""
    origins = cors_origins_from_env()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=bool(origins),
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
