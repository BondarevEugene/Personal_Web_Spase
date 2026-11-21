"""Isolated customer-portal DB. Use Neon URL from environment, never commit it."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parent.parent


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    return (os.getenv("OMNI_PORTAL_DATABASE_URL") or
            f"sqlite:///{(ROOT / 'portal_dev.sqlite3').as_posix()}")


def migration_url() -> str:
    url = os.getenv("OMNI_PORTAL_MIGRATION_URL") or database_url()
    if "-pooler." in url and url.startswith("postgresql"):
        raise RuntimeError("Use a DIRECT Neon URL for schema migrations (OMNI_PORTAL_MIGRATION_URL)")
    return url


@lru_cache(maxsize=1)
def engine():
    url = database_url()
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


@lru_cache(maxsize=1)
def session_factory():
    return sessionmaker(bind=engine(), autoflush=False, expire_on_commit=False)
