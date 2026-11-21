"""Read-only deployment acceptance checks for the modern OmniFactory portal.

Run only against a staging URL. No authentication, mutations or secret values.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass(frozen=True)
class Check:
    path: str
    expected: tuple[int, ...]
    marker: str | None = None


CHECKS = (
    Check("/health", (200,), '"platform_ui":"studio-v3-platform"'),
    Check("/", (200,), "OMNIFACTORY"),
    Check("/services", (200,), None),
    Check("/services/ai-solutions", (200,), None),
    Check("/demo", (200,), "data-demo-tab"),
    Check("/architect", (200,), None),
    Check("/automation/studio", (200,), None),
    Check("/account", (200, 302, 303, 307, 308), None),
    Check("/studio-assets/site.css", (200,), None),
    Check("/studio-assets/solution_demo.js", (200,), None),
    Check("/studio-assets/blueprint_studio.js", (200,), None),
)


class NoRedirect(HTTPRedirectHandler):
    """Never follow redirects to external domains or login endpoints."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def validate_url(value: str, *, allow_local: bool = False) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" and not (
        allow_local and parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost"}
    ):
        raise ValueError("Staging URL must use HTTPS (localhost HTTP is test-only)")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query:
        raise ValueError("Invalid staging URL")
    if parsed.path not in ("", "/") or parsed.fragment:
        raise ValueError("Staging URL must be an origin, without a path")
    if parsed.hostname.lower() in {"omnifactory.up.railway.app", "www.omnifactory.up.railway.app"}:
        raise ValueError("Use a separate staging domain, not the production domain")
    return value.rstrip("/") + "/"


def check_endpoint(origin: str, check: Check, timeout: float = 12) -> dict:
    url = urljoin(origin, check.path.lstrip("/"))
    request = Request(url, headers={"User-Agent": "OmniFactory-Release-Smoke/1.0"})
    opener = build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            status = response.status
            body = response.read(2_000_000).decode("utf-8", errors="replace")
    except HTTPError as exc:
        status = exc.code
        body = ""
        if status not in (301, 302, 303, 307, 308):
            return {"path": check.path, "ok": False, "status": status}
    except (URLError, TimeoutError, OSError) as exc:
        return {"path": check.path, "ok": False, "error": type(exc).__name__}
    ok = status in check.expected
    if check.marker is not None:
        if check.path == "/health" and ok:
            try:
                ok = json.loads(body).get("platform_ui") == "studio-v3-platform"
            except (ValueError, TypeError):
                ok = False
        else:
            ok = ok and check.marker.lower() in body.lower()
    if check.path == "/" and ("MAIN_NODE" in body or "BUILDER_PRO" in body):
        ok = False
    return {"path": check.path, "ok": ok, "status": status}


def run(origin: str) -> list[dict]:
    return [check_endpoint(origin, check) for check in CHECKS]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Isolated staging origin")
    parser.add_argument("--allow-local", action="store_true")
    args = parser.parse_args(argv)
    try:
        origin = validate_url(args.base_url, allow_local=args.allow_local)
    except ValueError as exc:
        parser.error(str(exc))
    results = run(origin)
    print(json.dumps({"checks": results, "passed": sum(x["ok"] for x in results),
                      "total": len(results)}, ensure_ascii=False, indent=2))
    return 0 if all(x["ok"] for x in results) else 1


if __name__ == "__main__":
    sys.exit(main())
