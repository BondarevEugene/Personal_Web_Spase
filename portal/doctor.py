"""Local diagnostic: pinpoint HTML version and portal database without leaking secrets."""
from pathlib import Path
from portal.bootstrap import migration_config, portal_schema_status, ui_source_status
from portal.db import database_url

def main():
    source, studio_ui = ui_source_status()
    print("Root HTML file:", source)
    print("Root Studio v3 markers:", "OK" if studio_ui else "OLD/MISSING")
    url = database_url()
    print("Portal database kind:", "SQLite" if url.startswith("sqlite:") else "PostgreSQL/configured")
    if url.startswith("sqlite:"):
        from sqlalchemy.engine import make_url
        print("SQLite file:", make_url(url).database)
    try:
        ready, current, expected = portal_schema_status()
        print("Portal schema:", "READY" if ready else "MISSING/OUTDATED")
        print("Portal Alembic revision:", current or "none")
        print("Expected revision:", expected)
    except Exception as exc:
        print("Portal database check failed:", type(exc).__name__)
        print("No credentials were printed.")
    print("Root runtime fingerprint expected: X-Omni-UI: studio-v3-platform")

if __name__ == "__main__":
    main()
