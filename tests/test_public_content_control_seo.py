"""Operator CMS/SEO acceptance: drafts, publication, rollback, true search metrics."""
from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from omni_site.editorial import ARTICLES
from omni_site.search_metrics import parse_page_csv
from portal.db import engine, session_factory
from portal.models import Customer, PublicSearchMetric
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "editorial.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    command.upgrade(Config(str(ROOT / "portal_alembic.ini")), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(name):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    response = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name, "display_name": name,
        "email": name + "@cms.test", "organization": name + " company",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert response.status_code == 303, response.text
    return client


def csrf(client, url):
    response = client.get(url)
    assert response.status_code == 200, response.text[:500]
    return client.cookies.get("omni_portal_csrf")


def operator_account(db_ready, monkeypatch):
    client = register("contentowner")
    with session_factory()() as db:
        user = db.scalar(select(Customer).where(Customer.username == "contentowner"))
        monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", user.id)
    return client


def test_operator_only_access_to_editor_and_seo(db_ready, monkeypatch):
    client = register("ordinaryreader")
    assert client.get("/support/content").status_code == 403
    assert client.get("/support/content/" + ARTICLES[0].slug).status_code == 403
    assert TestClient(app).get("/support/content").status_code == 401
    with session_factory()() as db:
        user = db.scalar(select(Customer).where(Customer.username == "ordinaryreader"))
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", user.id)
    dashboard = client.get("/support/content")
    assert dashboard.status_code == 200
    assert "Контент и SEO" in dashboard.text
    assert "Реальная посещаемость неизвестна" not in dashboard.text
    assert "Реальная посещаемость" not in dashboard.text or "неизвестна" in dashboard.text.lower()
    assert "Поисковые показы" in dashboard.text
    assert "Контент и SEO" in client.get("/support/desk").text


def test_draft_never_leaks_until_publish_and_restore(db_ready, monkeypatch):
    editor = operator_account(db_ready, monkeypatch)
    slug = ARTICLES[0].slug
    url = "/support/content/" + slug
    public = "/journal/" + slug
    assert csrf(editor, url)
    base_page = editor.get(public)
    assert base_page.status_code == 200
    assert "Опубликованная инженерная заметка" not in base_page.text

    article = ARTICLES[0]
    data = {
        "csrf_token": editor.cookies.get("omni_portal_csrf"),
        "title": "Опубликованная инженерная заметка OMNIFACTORY",
        "excerpt": "Новый проверяемый текст о практической Python-архитектуре и проверке сценариев.",
        "heading": [section.heading for section in article.sections],
        "body": [section.body for section in article.sections],
    }
    assert editor.post(url + "/save", data={k: v for k, v in data.items()
                                           if k != "csrf_token"}).status_code == 403
    # A fresh GET issues a new CSRF cookie for each form; POST must use it.
    data["csrf_token"] = csrf(editor, url)
    saved = editor.post(url + "/save", data=data, follow_redirects=False)
    assert saved.status_code == 303, saved.text
    assert "Опубликованная инженерная заметка" not in editor.get(public).text
    preview = editor.get(url + "?preview=true")
    assert "Опубликованная инженерная заметка" in preview.text

    published = editor.post(url + "/publish", follow_redirects=False, data={
        "csrf_token": csrf(editor, url),
    })
    assert published.status_code == 303
    live = editor.get(public)
    assert "Опубликованная инженерная заметка" in live.text
    assert "Опубликованная инженерная заметка" in editor.get("/journal").text

    restored = editor.post(url + "/restore", follow_redirects=False, data={
        "csrf_token": csrf(editor, url),
    })
    assert restored.status_code == 303
    assert "Опубликованная инженерная заметка" not in editor.get(public).text
    assert article.title in editor.get(public).text


def test_untrusted_article_html_is_escaped(db_ready, monkeypatch):
    editor = operator_account(db_ready, monkeypatch)
    article = ARTICLES[0]
    url = "/support/content/" + article.slug
    data = {
        "csrf_token": csrf(editor, url),
        "title": "Safe journal story with scripts escaped",
        "excerpt": "<script>alert(1)</script> not executable in the public article body",
        "heading": [item.heading for item in article.sections],
        "body": [item.body for item in article.sections],
    }
    assert editor.post(url + "/save", data=data, follow_redirects=False).status_code == 303
    assert editor.post(url + "/publish", data={
        "csrf_token": csrf(editor, url),
    }, follow_redirects=False).status_code == 303
    page = editor.get("/journal/" + article.slug)
    assert "<script>alert(1)</script>" not in page.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page.text


def test_search_console_report_accepts_real_aggregate_only(db_ready, monkeypatch):
    editor = operator_account(db_ready, monkeypatch)
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    csv = ("Page,Clicks,Impressions,CTR,Position\n"
           "https://omni.example.com/,12,160,7.5%,9.2\n"
           "https://omni.example.com/journal,3,40,7.5%,14.5\n")
    response = editor.post(
        "/support/content/search-console/import",
        data={"csrf_token": csrf(editor, "/support/content"),
              "report_date": "2026-11-19"},
        files={"report": ("pages.csv", csv.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    panel = editor.get("/support/content")
    assert "15" in panel.text
    assert "200" in panel.text
    assert "7.50" in panel.text
    assert "2026-11-19" in panel.text
    with session_factory()() as db:
        records = db.scalars(select(PublicSearchMetric)).all()
        assert len(records) == 2
        assert sum(record.clicks for record in records) == 15

    repeated = editor.post(
        "/support/content/search-console/import",
        data={"csrf_token": csrf(editor, "/support/content"),
              "report_date": "2026-11-19"},
        files={"report": ("pages.csv", csv.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    assert repeated.status_code == 303
    with session_factory()() as db:
        assert len(db.scalars(select(PublicSearchMetric)).all()) == 2


@pytest.mark.parametrize("report", [
    b"Page,Clicks,Impressions\nhttps://evil.example.com/,1,2\n",
    b"Page,Clicks,Impressions\nhttps://omni.example.com/account,1,2\n",
    b"Page,Clicks,Impressions\nhttps://omni.example.com/,3,2\n",
    b"Page,Clicks,Impressions\nhttps://omni.example.com/?secret=1,1,2\n",
    b"Page,Clicks,Impressions\nhttps://omni.example.com/,1,2\n"
    b"https://omni.example.com/,1,2\n",
    b"Person,Email,Clicks\nSomeone,a@example.com,12\n",
])
def test_search_import_rejects_invalid_or_private_urls(report):
    with pytest.raises(ValueError):
        parse_page_csv(report, "https://omni.example.com", "2026-11-19")


def test_search_import_denies_nonoperator_without_writes(db_ready, monkeypatch):
    person = register("outsideperson")
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    token = csrf(person, "/account")
    upload = person.post(
        "/support/content/search-console/import",
        data={"csrf_token": token, "report_date": "2026-11-19"},
        files={"report": ("pages.csv",
               b"Page,Clicks,Impressions\nhttps://omni.example.com/,1,2\n",
               "text/csv")},
    )
    assert upload.status_code == 403
    with session_factory()() as db:
        assert db.scalars(select(PublicSearchMetric)).all() == []
