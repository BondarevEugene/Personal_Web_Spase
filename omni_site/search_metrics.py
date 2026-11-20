"""Import only aggregate, first-party Search Console page reports.

No cookies, user-agent, IP address, visitor IDs, or client-side tracking.
All CSV rows are parsed and checked before any database writes.
"""
from __future__ import annotations

import csv
import io
import math
from datetime import date
from urllib.parse import urlsplit

from sqlalchemy import func, select

from omni_site.case_library import CASES
from omni_site.editorial import ARTICLES
from omni_site.search_discovery import PUBLIC_PATHS, canonical_origin
from omni_site.services_catalog import SERVICES
from omni_site.trust_content import PAGES
from portal.models import PublicSearchMetric, utcnow

MAX_REPORT_BYTES = 512 * 1024
MAX_ROWS = 2000


def allowed_paths() -> set[str]:
    return {
        *PUBLIC_PATHS,
        *(f"/journal/{a.slug}" for a in ARTICLES),
        *(f"/cases/{a.slug}" for a in CASES),
        *(f"/services/{a.slug}" for a in SERVICES),
        *(f"/trust/{a.slug}" for a in PAGES),
    }


def parse_page_csv(blob: bytes, origin: str, day: str) -> list[PublicSearchMetric]:
    if not blob or len(blob) > MAX_REPORT_BYTES:
        raise ValueError("CSV file must be 1-524288 bytes")
    base = canonical_origin(origin)
    if base is None:
        raise ValueError("Set a valid OMNI_PUBLIC_BASE_URL HTTPS origin first")
    try:
        parsed_day = date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError("Report date must be YYYY-MM-DD") from exc
    if parsed_day.isoformat() != day or parsed_day > date.today():
        raise ValueError("Report date is invalid or in the future")
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Export CSV as UTF-8") from exc
    if "\x00" in text:
        raise ValueError("Invalid CSV")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise ValueError("CSV header missing")
    headers = {header.strip().lower(): header for header in reader.fieldnames}
    page_col = headers.get("page") or headers.get("top pages")
    clicks_col = headers.get("clicks")
    impressions_col = headers.get("impressions")
    position_col = headers.get("position")
    if not all((page_col, clicks_col, impressions_col)):
        raise ValueError("Expected Page, Clicks, Impressions columns")
    permitted = allowed_paths()
    host = urlsplit(base).netloc.lower()
    rows: list[PublicSearchMetric] = []
    seen: set[str] = set()
    for number, entry in enumerate(reader, 1):
        if number > MAX_ROWS:
            raise ValueError("Maximum 2000 rows")
        raw_url = (entry.get(page_col) or "").strip()
        url = urlsplit(raw_url)
        if (url.scheme != "https" or url.netloc.lower() != host
                or url.query or url.fragment or url.username or url.password):
            raise ValueError("Unexpected origin or URL in report")
        path = url.path or "/"
        if path not in permitted or path in seen:
            raise ValueError("Duplicate, unknown, or private path in report")
        seen.add(path)
        try:
            clicks = int((entry.get(clicks_col) or "").replace(",", ""))
            impressions = int((entry.get(impressions_col) or "").replace(",", ""))
            position = (
                float(entry[position_col]) if position_col and entry.get(position_col)
                else None
            )
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid numeric metric") from exc
        if (clicks < 0 or impressions < clicks or impressions > 2_000_000_000
                or (position is not None and (
                    not math.isfinite(position) or not 0 <= position <= 1000
                ))):
            raise ValueError("Metric value out of range")
        rows.append(PublicSearchMetric(
            date=day, path=path, clicks=clicks,
            impressions=impressions, position=position, imported_at=utcnow(),
        ))
    if not rows:
        raise ValueError("No report rows found")
    return rows


def store_metrics(db, values: list[PublicSearchMetric]) -> None:
    for row in values:
        db.merge(row)


def report_summary(db) -> dict:
    latest = db.scalar(select(func.max(PublicSearchMetric.date)))
    if latest is None:
        return {"day": None, "clicks": 0, "impressions": 0, "ctr": 0.0,
                "rows": [], "position": None}
    rows = db.scalars(
        select(PublicSearchMetric).where(
            PublicSearchMetric.date == latest,
        ).order_by(PublicSearchMetric.clicks.desc()).limit(MAX_ROWS),
    ).all()
    clicks = sum(row.clicks for row in rows)
    impressions = sum(row.impressions for row in rows)
    positions = [row for row in rows if row.position is not None and row.impressions]
    weighted_position = (
        sum(row.position * row.impressions for row in positions)
        / sum(row.impressions for row in positions)
        if positions else None
    )
    return {
        "day": latest, "clicks": clicks, "impressions": impressions,
        "ctr": 100 * clicks / impressions if impressions else 0.0,
        "position": weighted_position,
        "rows": rows[:25],
    }
