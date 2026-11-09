"""Validate the *separate* customer portal schema at application startup.

Only the default local SQLite development database is migrated automatically.
Neon/PostgreSQL and explicitly configured databases are NEVER changed on startup.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from portal.db import database_url, engine

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent


class PortalSchemaNotReady(RuntimeError):
    pass


def migration_config() -> Config:
    cfg = Config(str(ROOT / "portal_alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "portal" / "migrations"))
    return cfg


def portal_schema_status() -> tuple[bool, str | None, str]:
    """Return (ready, actual revision, expected revision), without DSN logging."""
    cfg = migration_config()
    expected = ScriptDirectory.from_config(cfg).get_current_head()
    with engine().connect() as conn:
        actual = MigrationContext.configure(conn).get_current_revision()
        tables = set(inspect(conn).get_table_names())
    return ("portal_customers" in tables and actual == expected, actual, expected)


def ensure_portal_database() -> None:
    """Auto-migrate local development only, otherwise fail BEFORE accepting signups."""
    url = database_url()
    explicit = bool(os.environ.get("OMNI_PORTAL_DATABASE_URL"))
    is_local_sqlite = url.startswith("sqlite:")
    may_auto_migrate = is_local_sqlite and (
        not explicit or os.getenv("OMNI_PORTAL_DEV_AUTO_MIGRATE") == "1"
    )

    try:
        ready, actual, expected = portal_schema_status()
        if ready:
            log.info("Customer portal database ready (schema %s; %s).",
                     expected, "local SQLite" if is_local_sqlite else "configured database")
            return
        if not may_auto_migrate:
            raise PortalSchemaNotReady(
                "Customer portal schema is missing/outdated "
                f"(revision {actual or 'none'}, expected {expected}). "
                "Apply: python -m alembic -c portal_alembic.ini upgrade head "
                "against the configured portal database (direct Neon migration URL)."
            )
        log.warning("Local development portal schema %s -> %s; applying Alembic migrations.",
                    actual or "none", expected)
        command.upgrade(migration_config(), "head")
        ready, actual, expected = portal_schema_status()
        if not ready:
            raise PortalSchemaNotReady(
                "Customer portal migration finished but the expected tables/revision "
                "were not found. Check the portal DB URL and Alembic configuration."
            )
        log.info("Local customer portal database initialized (revision %s).", expected)
    except PortalSchemaNotReady:
        raise
    except Exception as exc:
        # Never log the SQLAlchemy exception/connection URL (may include credentials).
        raise PortalSchemaNotReady(
            "Customer portal database initialization failed. "
            "Check OMNI_PORTAL_DATABASE_URL / OMNI_PORTAL_MIGRATION_URL, "
            "and run: python -m alembic -c portal_alembic.ini upgrade head. "
            f"Reason type: {type(exc).__name__}."
        ) from None


def ui_source_status() -> tuple[str, bool]:
    """Surface the *real on-disk* HTML used by the root page, without revealing secrets."""
    index = ROOT / "index.html"
    if not index.is_file():
        return (str(index), False)
    content = index.read_text(encoding="utf-8", errors="replace")
    return (str(index), "studio-assets/platform.css" in content and
            'class="platform-app"' in content)
