"""Safe versioned journal content overlay.

Draft content is never public. Only allowlisted first-party slugs can be
edited. Original checked-in articles remain the fallback and rollback source.
"""
from __future__ import annotations

import json
from dataclasses import replace

from sqlalchemy import select

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG, Article, Section
from portal.models import PublicArticleRevision


def section_json(sections: tuple[Section, ...]) -> str:
    return json.dumps(
        [{"heading": item.heading, "body": item.body} for item in sections],
        ensure_ascii=False,
    )


def parse_sections(data: str) -> tuple[Section, ...]:
    """Strict plain-text structure; no HTML/Markdown renderer is involved."""
    raw = json.loads(data)
    if not isinstance(raw, list) or not 2 <= len(raw) <= 8:
        raise ValueError("Require 2-8 sections")
    sections = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) != {"heading", "body"}:
            raise ValueError("Invalid section structure")
        heading, body = entry["heading"], entry["body"]
        if not isinstance(heading, str) or not isinstance(body, str):
            raise ValueError("Invalid section value")
        heading, body = heading.strip(), body.strip()
        if not 5 <= len(heading) <= 140 or not 50 <= len(body) <= 4000:
            raise ValueError("Section length is out of bounds")
        sections.append(Section(heading=heading, body=body))
    return tuple(sections)


def overlay(article: Article, title: str, excerpt: str, sections: str) -> Article:
    return replace(
        article,
        title=title, excerpt=excerpt, sections=parse_sections(sections),
    )


def published_article(db, slug: str) -> Article | None:
    original = ARTICLE_BY_SLUG.get(slug)
    if original is None:
        return None
    revision = db.get(PublicArticleRevision, slug)
    if revision is None or revision.published_at is None:
        return original
    if not all((
        revision.published_title, revision.published_excerpt,
        revision.published_sections,
    )):
        return original
    return overlay(
        original, revision.published_title, revision.published_excerpt,
        revision.published_sections,
    )


def public_articles(db) -> tuple[Article, ...]:
    return tuple(published_article(db, item.slug) for item in ARTICLES)


def save_draft(db, slug: str, title: str, excerpt: str, sections: str, author: str):
    original = ARTICLE_BY_SLUG[slug]
    if not 12 <= len(title) <= 180 or not 30 <= len(excerpt) <= 450:
        raise ValueError("Title or excerpt length out of bounds")
    overlay(original, title, excerpt, sections)
    revision = db.get(PublicArticleRevision, slug)
    if revision is None:
        revision = PublicArticleRevision(
            slug=slug, draft_title=title,
            draft_excerpt=excerpt, draft_sections=sections,
        )
        db.add(revision)
    else:
        revision.draft_title = title
        revision.draft_excerpt = excerpt
        revision.draft_sections = sections
    from portal.models import utcnow

    revision.updated_by_id = author
    revision.updated_at = utcnow()
    db.flush()
    return revision


def publish(db, slug: str, author: str) -> None:
    from portal.models import utcnow

    revision = db.scalar(
        select(PublicArticleRevision).where(
            PublicArticleRevision.slug == slug,
        ).with_for_update(),
    )
    if revision is None:
        raise ValueError("Create and review a draft before publishing")
    overlay(
        ARTICLE_BY_SLUG[slug], revision.draft_title,
        revision.draft_excerpt, revision.draft_sections,
    )
    revision.published_title = revision.draft_title
    revision.published_excerpt = revision.draft_excerpt
    revision.published_sections = revision.draft_sections
    revision.published_at = utcnow()
    revision.updated_by_id = author


def restore_original(db, slug: str) -> None:
    revision = db.scalar(
        select(PublicArticleRevision).where(
            PublicArticleRevision.slug == slug,
        ).with_for_update(),
    )
    if revision is not None:
        revision.published_title = None
        revision.published_excerpt = None
        revision.published_sections = None
        revision.published_at = None
