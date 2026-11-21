"""Regression checks for public SEO discovery endpoints."""

from xml.etree import ElementTree

import pytest

from omni_site import search_discovery


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://omnifactory.example", "https://omnifactory.example"),
        ("https://omnifactory.example/", "https://omnifactory.example"),
        ("http://omnifactory.example", None),
        ("https://user:pass@omnifactory.example", None),
        ("https://omnifactory.example/path", None),
        ("https://omnifactory.example/?q=1", None),
        ("https://omnifactory.example/#fragment", None),
        ("https://omnifactory.example:0", None),
        ("https://omni factory.example", None),
    ],
)
def test_canonical_origin_requires_safe_configured_https(value, expected):
    assert search_discovery.canonical_origin(value) == expected


def test_sitemap_unavailable_without_explicit_public_host(monkeypatch):
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert search_discovery.sitemap().status_code == 404


def test_sitemap_is_well_formed_unique_and_uses_configured_host(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omnifactory.example")
    response = search_discovery.sitemap()
    assert response.status_code == 200
    root = ElementTree.fromstring(response.body)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [
        element.text for element in root.findall("sm:url/sm:loc", namespace)
    ]
    assert locations
    assert len(locations) == len(set(locations))
    assert "https://omnifactory.example/studio" in locations
    assert all(url.startswith("https://omnifactory.example/") for url in locations)
    assert not any("/account/" in url or "/api/" in url for url in locations)


def test_robots_blocks_private_sections_and_announces_sitemap(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omnifactory.example")
    response = search_discovery.robots()
    text = response.body.decode("utf-8")
    assert "Disallow: /account" in text
    assert "Disallow: /api" in text
    assert "Disallow: /dashboard" in text
    assert "Disallow: /docs" in text
    assert "Sitemap: https://omnifactory.example/sitemap.xml" in text
