"""Public Chromium regression and measured visual-quality report.

Usage:
    python -m scripts.public_ux_audit --base-url http://127.0.0.1:8765

Only loopback origins are accepted. The script does not authenticate, visit
private files, submit leads, or communicate analytics to third-party servers.
"""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

ROUTES = (
    "/",
    "/services",
    "/services/custom-crm",
    "/cases",
    "/cases/graph-studio",
    "/journal",
    "/trust",
    "/demo",
    "/demo/telegram",
    "/demo/blueprint",
)
VIEWPORTS = (360, 430, 768, 1440)


def validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise ValueError("Audit URL must be a local http:// host with port")
    return value.rstrip("/")


def summarize(rows: list[dict]) -> dict:
    failed = [
        {"route": row["route"], "width": row["width"],
         "issues": row["issues"]}
        for row in rows if row["issues"]
    ]
    first_view = next(
        (row for row in rows if row["route"] == "/" and
         row["width"] == 1440),
        None,
    )
    return {
        "checked": len(rows),
        "failed": len(failed),
        "failures": failed,
        "homepage_desktop": first_view,
    }


def audit(base_url: str, output: Path) -> int:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=True)
    screenshots = output / "screenshots"
    screenshots.mkdir(exist_ok=True)
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": 860},
                device_scale_factor=1,
                reduced_motion="reduce",
                service_workers="block",
            )
            for route in ROUTES:
                page = context.new_page()
                exceptions = []
                def collect_page_error(error, target=exceptions):
                    target.append(str(error))

                page.on("pageerror", collect_page_error)
                issues = []
                try:
                    response = page.goto(
                        base_url + route,
                        wait_until="domcontentloaded",
                        timeout=20_000,
                    )
                    if response is None or response.status != 200:
                        issues.append("page HTTP status is not 200")
                    page.locator("h1").first.wait_for(timeout=8_000)
                    geometry = page.evaluate(
                        """() => ({
                          viewport: document.documentElement.clientWidth,
                          content: document.documentElement.scrollWidth,
                          title: document.title,
                          links: [...document.querySelectorAll(
                            'a[href^="/"]'
                          )].length,
                          navigation: performance.getEntriesByType(
                            'navigation'
                          )[0]?.duration ?? null,
                          resources: performance.getEntriesByType(
                            'resource'
                          ).length
                        })"""
                    )
                    if geometry["content"] > geometry["viewport"] + 2:
                        suspects = page.evaluate(
                            """() => [...document.querySelectorAll("body *")]
                              .filter(el => {
                                const r = el.getBoundingClientRect();
                                const v = document.documentElement.clientWidth;
                                return r.width > 0 &&
                                  (r.right > v + 2 || r.left < -2);
                              })
                              .slice(0, 12).map(el => ({
                                tag: el.tagName.toLowerCase(),
                                css: String(el.className).slice(0, 90),
                                right: Math.round(el.getBoundingClientRect().right),
                                left: Math.round(el.getBoundingClientRect().left)
                              }))"""
                        )
                        issues.append(
                            "horizontal overflow: " +
                            str(geometry["content"]) + " > " +
                            str(geometry["viewport"]) +
                            " suspects=" + json.dumps(suspects)
                        )
                    if not geometry["title"]:
                        issues.append("missing document title")
                    if route == "/":
                        if page.locator(
                            ".omni-hero-pathways a"
                        ).count() != 3:
                            issues.append("hero business routes missing")
                        if width <= 430:
                            contact = page.locator(".omni-mobile-contact")
                            if not contact.is_visible():
                                issues.append("mobile contact CTA hidden")
                            menu = page.locator("#menu-toggle")
                            if not menu.is_visible():
                                issues.append("mobile menu toggle hidden")
                            else:
                                menu.click()
                                if menu.get_attribute(
                                    "aria-expanded"
                                ) != "true":
                                    issues.append(
                                        "mobile navigation failed to open"
                                    )
                    if route in ("/demo", "/demo/telegram"):
                        if page.locator(
                            "[data-demo-tab]"
                        ).count() != 4:
                            issues.append("demo scenarios missing")
                        else:
                            page.locator(
                                '[data-demo-tab="automation"]'
                            ).click()
                            if not page.locator(
                                '[data-demo-panel="automation"]'
                            ).is_visible():
                                issues.append("demo tab did not switch")
                            node = page.locator(
                                '[data-demo-panel="automation"] '
                                '[data-demo-step="1"]'
                            )
                            node.click()
                            heading = page.locator(
                                '[data-demo-panel="automation"] '
                                '[data-demo-current-title]'
                            ).inner_text()
                            if heading != "Условия":
                                issues.append("demo inspector stale")
                    if route == "/demo/blueprint" and width <= 430:
                        file_picker = page.locator("#blueprint-plan-file")
                        if not file_picker.count():
                            issues.append("Blueprint JSON import picker missing")
                        else:
                            bounds = file_picker.bounding_box()
                            if (
                                bounds is None
                                or bounds["x"] < -2
                                or bounds["x"] + bounds["width"] > width + 2
                            ):
                                issues.append(
                                    "Blueprint JSON import picker overflows mobile viewport"
                                )
                    if route == "/demo/blueprint":
                        if page.locator("#blueprint-form").count() != 1:
                            issues.append("Blueprint form missing")
                        else:
                            page.locator("#blueprint-form button[type=submit]").click()
                            page.locator("#blueprint-result").wait_for(
                                timeout=8_000,
                            )
                            if not page.locator("#blueprint-output").input_value():
                                issues.append("Blueprint result text missing")
                            if page.locator(
                                ".blueprint-content-grid .blueprint-block"
                            ).count() != 4:
                                issues.append("Blueprint architecture panels missing")
                    if route == "/services" and not page.locator(
                        'a[href="/services/custom-crm"]'
                    ).count():
                        issues.append("service catalogue link missing")
                    if route == "/cases" and not page.locator(
                        'a[href="/cases/graph-studio"]'
                    ).count():
                        issues.append("case catalogue link missing")
                    if route != "/" and width <= 430:
                        summary = page.locator(
                            ".omni-mobile-menu summary"
                        )
                        if not summary.is_visible():
                            issues.append("public mobile menu hidden")
                        else:
                            summary.click()
                            if not page.locator(
                                ".omni-mobile-menu"
                            ).evaluate(
                                "(el) => el.open"
                            ):
                                issues.append("native mobile menu failed")
                    if (
                        route == "/" and width in (360, 1440)
                    ) or (
                        route == "/demo" and width == 360
                    ):
                        name = (
                            (route.replace("/", "_") or "home")
                            + "_" + str(width) + ".png"
                        )
                        page.screenshot(
                            path=str(screenshots / name),
                            full_page=True,
                            animations="disabled",
                        )
                except (PlaywrightError, ValueError, RuntimeError) as exc:
                    issues.append(
                        "browser exception: " + str(exc)[:240]
                    )
                    geometry = {}
                issues.extend(
                    "JavaScript exception: " + err[:200]
                    for err in exceptions
                )
                rows.append({
                    "route": route,
                    "width": width,
                    "issues": issues,
                    "geometry": geometry,
                })
                page.close()
            context.close()
        browser.close()
    result = summarize(rows)
    result["generated_at_utc"] = datetime.now(
        UTC
    ).isoformat()
    result["limits"] = (
        "Browser smoke, layout overflow, navigation and JS exceptions. "
        "Not a production Core Web Vitals measurement or SEO ranking."
    )
    (output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    text = [
        "# OMNIFACTORY — Chromium public UX audit",
        "",
        f"Checked views: {result['checked']}",
        f"Failures: {result['failed']}",
        "",
        "| Page | Viewport | Finding |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        label = "; ".join(row["issues"]) if row["issues"] else "PASS"
        text.append(
            f"| {row['route']} | {row['width']}px | "
            f"{label.replace('|', '/')} |"
        )
    text.extend([
        "", "## Scope",
        result["limits"],
        "",
        "The screenshot set contains only public, demonstration pages.",
    ])
    (output / "report.md").write_text(
        "\n".join(text) + "\n", encoding="utf-8"
    )
    for failure in result["failures"]:
        print("UX FAIL:", json.dumps(failure, ensure_ascii=False))
    print(
        f"Public UX audit: {result['checked']} views, "
        f"{result['failed']} failed; report={output / 'report.md'}"
    )
    return 1 if result["failed"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8765"
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("artifacts/public-ux"),
    )
    args = parser.parse_args()
    return audit(validate_base_url(args.base_url), args.output)


if __name__ == "__main__":
    raise SystemExit(main())
