"""SEO metadata rendering regression tests without database dependencies."""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from omni_site.search_discovery import canonical_origin

TEMPLATES = Path(__file__).resolve().parents[1] / "omni_site" / "templates"


def test_shared_metadata_uses_explicit_origin_and_valid_jsonld():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("_seo_detail_meta.html")
    rendered = template.render(
        seo_origin=canonical_origin("https://omnifactory.example"),
        seo_path="/services/crm",
        seo_title='CRM "Enterprise"',
        seo_description="Custom CRM & automation",
        seo_schema_type="Service",
    )
    assert 'rel="canonical" href="https://omnifactory.example/services/crm"' in rendered
    assert 'property="og:url"' in rendered
    payload = rendered.split('<script type="application/ld+json">', 1)[1].split(
        "</script>", 1
    )[0]
    data = json.loads(payload)
    assert data["@type"] == "Service"
    assert data["headline"] == 'CRM "Enterprise"'
    assert data["publisher"]["name"] == "OMNIFACTORY"


def test_metadata_omitted_without_configured_public_domain():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    rendered = env.get_template("_seo_detail_meta.html").render(
        seo_origin=None,
        seo_path="/cases/example",
        seo_title="Example",
        seo_description="Description",
        seo_schema_type="CreativeWork",
    )
    assert 'rel="canonical"' not in rendered
    assert "application/ld+json" not in rendered


def test_public_detail_templates_include_shared_metadata():
    for name in (
        "service_detail.html",
        "case_detail.html",
        "engineering_article.html",
    ):
        source = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "{% include '_seo_detail_meta.html' %}" in source
