"""Creative Content Studio: safe editorial overrides without client-side scripts.

Only known service and case records may be edited; original product links,
technical scope, disclaimers, slugs, and source references remain immutable.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from sqlalchemy.exc import OperationalError

from omni_site.case_library import CASES, CASE_BY_SLUG
from omni_site.services_catalog import SERVICES, SERVICE_BY_SLUG
from portal.models import PublicPageRevision, utcnow


def catalog():
    return {
        **{"service:" + item.slug: item for item in SERVICES},
        **{"case:" + item.slug: item for item in CASES},
    }


def source(page_key: str):
    return catalog().get(page_key)


def validate_copy(title: str, summary: str) -> tuple[str, str]:
    title, summary = title.strip(), summary.strip()
    if not 12 <= len(title) <= 180:
        raise ValueError("Title must be 12-180 characters")
    if not 40 <= len(summary) <= 800:
        raise ValueError("Summary must be 40-800 characters")
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in title + summary):
        raise ValueError("Control characters are not allowed")
    return title, summary


def effective_copy(record: PublicPageRevision | None):
    if record is None:
        return None
    if (record.scheduled_for is not None
            and record.scheduled_for <= utcnow()
            and record.scheduled_title and record.scheduled_summary):
        return record.scheduled_title, record.scheduled_summary
    if record.published_at and record.published_title and record.published_summary:
        return record.published_title, record.published_summary
    return None


def apply_override(item, copy):
    if copy is None:
        return item
    title, summary = copy
    return replace(item, title=title, summary=summary)


def read_override(db, page_key: str):
    if page_key not in catalog():
        return None
    try:
        record = db.get(PublicPageRevision, page_key)
    except OperationalError:
        # Existing public pages should remain available on old local DBs.
        db.rollback()
        return None
    return effective_copy(record)


def public_items(db, category: str):
    if category == "services":
        return tuple(apply_override(item, read_override(db, "service:" + item.slug))
                     for item in SERVICES)
    if category == "cases":
        return tuple(apply_override(item, read_override(db, "case:" + item.slug))
                     for item in CASES)
    raise ValueError("Unknown category")


def public_item(db, category: str, slug: str):
    if category == "services":
        original = SERVICE_BY_SLUG.get(slug)
        prefix = "service:"
    elif category == "cases":
        original = CASE_BY_SLUG.get(slug)
        prefix = "case:"
    else:
        raise ValueError("Unknown category")
    if original is None:
        return None
    return apply_override(original, read_override(db, prefix + slug))


def save_draft(db, page_key: str, title: str, summary: str, user_id: str):
    if source(page_key) is None:
        raise ValueError("Unknown page")
    title, summary = validate_copy(title, summary)
    record = db.get(PublicPageRevision, page_key)
    if record is None:
        record = PublicPageRevision(
            page_key=page_key, draft_title=title, draft_summary=summary,
        )
        db.add(record)
    else:
        record.draft_title, record.draft_summary = title, summary
    record.updated_by_id, record.updated_at = user_id, utcnow()
    db.flush()
    return record


def publish(db, page_key: str, user_id: str, at: datetime | None = None):
    from sqlalchemy import select

    record = db.scalar(select(PublicPageRevision).where(
        PublicPageRevision.page_key == page_key,
    ).with_for_update())
    if record is None:
        raise ValueError("Save a draft before publishing")
    validate_copy(record.draft_title, record.draft_summary)
    now = utcnow()
    if at is not None and at > now:
        record.scheduled_title = record.draft_title
        record.scheduled_summary = record.draft_summary
        record.scheduled_for = at
    else:
        record.published_title = record.draft_title
        record.published_summary = record.draft_summary
        record.published_at = now
        record.scheduled_title = None
        record.scheduled_summary = None
        record.scheduled_for = None
    record.updated_by_id, record.updated_at = user_id, now


def restore(db, page_key: str, user_id: str):
    from sqlalchemy import select

    record = db.scalar(select(PublicPageRevision).where(
        PublicPageRevision.page_key == page_key,
    ).with_for_update())
    if record is None:
        return
    record.published_title = None
    record.published_summary = None
    record.published_at = None
    record.scheduled_title = None
    record.scheduled_summary = None
    record.scheduled_for = None
    record.updated_by_id, record.updated_at = user_id, utcnow()
