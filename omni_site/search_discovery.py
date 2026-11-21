"""Public indexing endpoints. The canonical host must be explicitly configured."""
from __future__ import annotations

import os
from urllib.parse import quote, urlsplit
from xml.sax.saxutils import escape

from fastapi import APIRouter

from omni_site.editorial import ARTICLES
from omni_site.case_library import CASES
from omni_site.services_catalog import SERVICES
from omni_site.trust_content import PAGES
from omni_site.solution_journeys import JOURNEYS
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(tags=["Public Search Discovery"])
PUBLIC_PATHS = (
    "/", "/studio", "/projects", "/robotization", "/techkillers", "/journal", "/cases", "/services", "/trust", "/demo", "/demo/blueprint",
)
PRIVATE_PREFIXES = (
    "/account", "/support", "/api", "/bots", "/admin", "/cloud",
    "/dashboard", "/automation/studio", "/docs", "/redoc", "/openapi.json",
)


def canonical_origin(value: str) -> str | None:
    """Reject userinfo, fragments, ports outside URL syntax and path segments."""
    try:
        parsed = urlsplit(value.strip())
        if (parsed.scheme != "https" or not parsed.hostname
                or parsed.username or parsed.password
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            return None
        if any(char.isspace() for char in value) or parsed.port == 0:
            return None
        # This origin is configured by the operator, never inferred from Host.
        return value.strip().rstrip("/")
    except ValueError:
        return None


@router.get("/robots.txt", include_in_schema=False)
def robots():
    origin = canonical_origin(os.getenv("OMNI_PUBLIC_BASE_URL", ""))
    lines = ["User-agent: *"]
    lines.extend("Disallow: " + prefix for prefix in PRIVATE_PREFIXES)
    lines.extend(["Allow: /", ""])
    if origin:
        lines.append("Sitemap: " + origin + "/sitemap.xml")
    return PlainTextResponse("\n".join(lines) + "\n")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    origin = canonical_origin(os.getenv("OMNI_PUBLIC_BASE_URL", ""))
    if origin is None:
        return Response(status_code=404)
    paths = (*PUBLIC_PATHS, *(f"/journal/{quote(article.slug, safe='')}" for article in ARTICLES),
             *(f"/cases/{quote(item.slug, safe='')}" for item in CASES),
             *(f"/services/{quote(service.slug, safe='')}" for service in SERVICES),
             *(f"/trust/{quote(page.slug, safe='')}" for page in PAGES),
             *(f"/demo/{quote(journey.slug, safe='')}" for journey in JOURNEYS))
    urls = "\n".join(
        "  <url><loc>" + escape(origin + path) + "</loc></url>"
        for path in dict.fromkeys(paths)
    )
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += urls + "\n</urlset>\n"
    return Response(body, media_type="application/xml")
