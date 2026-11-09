# -*- coding: utf-8 -*-
"""OmniFactory Platform | Safe, Python-only ASGI launcher.

PURPOSE
    Start the EXISTING ``server:app`` without changing FastAPI routes,
    middleware, database initialization or the application lifespan.

COMMANDS
    python run.py                  Start the platform on port 8000.
    python run.py --port 8001      Use another port (overrides PORT).
    python run.py --open           Open /studio in the browser after startup.
    python run.py --check          Check an already running platform.
    python run.py --doctor         Inspect environment, dependencies and URLs.
    python run.py --watch          Report /health state changes periodically.

NOTES
    - Does not kill or restart other processes.
    - URL probes are informational: a 404/500 does NOT stop the platform.
    - HTTP links use 127.0.0.1 for local browser access; Uvicorn binds to
      0.0.0.0 so container and Cloud Run networking continue to work.
    - Uses only Python's standard library plus the project's existing Uvicorn.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parent
ROUTES = (
    ("Главная", "/"),
    ("Сайт студии", "/studio"),
    ("Документация API", "/docs"),
    ("Проверка сервера", "/health"),
)
STARTED_AT = time.monotonic()


class Palette:
    """Terminal styling; falls back to readable plain text when redirected."""

    enabled = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    RESET = "\033[0m"
    CYAN = "\033[96m"
    VIOLET = "\033[95m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    DIM = "\033[90m"
    BOLD = "\033[1m"

    @classmethod
    def paint(cls, text: str, style: str) -> str:
        return f"{style}{text}{cls.RESET}" if cls.enabled else text


def log(message: str, style: str = "") -> None:
    """Write a UTF-8 friendly log line with the OmniFactory prefix."""

    print(Palette.paint("[OMNI]", Palette.VIOLET) + " " +
          (Palette.paint(message, style) if style else message), flush=True)


def separator() -> None:
    print(Palette.paint("═" * 76, Palette.DIM), flush=True)


def banner(port: int, host: str) -> None:
    """Display diagnostic boot header, without importing the FastAPI app."""

    print()
    separator()
    print(Palette.paint("  ◈  O M N I F A C T O R Y    /    PLATFORM BIOS", Palette.CYAN))
    print(Palette.paint("     PYTHON ENGINEERING  •  AI SYSTEMS  •  AUTOMATION", Palette.DIM))
    separator()
    log(f"Python {platform.python_version()}  |  PID {os.getpid()}  |  {platform.system()}")
    log(f"Workspace: {PROJECT_ROOT.name}")
    branch = git_branch()
    if branch:
        log(f"Git branch: {branch}")
    log(f"Listening on {host}:{port}  |  Ctrl+C = graceful shutdown")


def git_branch() -> str | None:
    """Return the branch if Git is installed, without failing startup."""

    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return result.stdout.strip() or None if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def local_base(port: int) -> str:
    """Generate local browser address (never use 0.0.0.0 as a browser URL)."""

    return f"http://127.0.0.1:{port}"


def endpoints(port: int) -> tuple[tuple[str, str], ...]:
    """Return the four canonical links, adapting to an alternative PORT."""

    return tuple((label, local_base(port) + path) for label, path in ROUTES)


def probe(url: str, timeout: float = 1.75) -> tuple[int | None, float, str]:
    """HTTP GET: return (status, milliseconds, error) without throwing.

    Reading only a byte ensures a large HTML page is not downloaded by the
    launcher. 4xx/5xx are preserved as statuses to aid route diagnostics.
    """

    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "OmniFactory-Launcher/2", "Cache-Control": "no-cache"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1)
            status = response.status
        return status, (time.perf_counter() - started) * 1000, ""
    except urllib.error.HTTPError as exc:
        return exc.code, (time.perf_counter() - started) * 1000, exc.reason or "HTTP error"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, (time.perf_counter() - started) * 1000, str(exc)


def print_links(port: int, *, check: bool = False) -> dict[str, int | None]:
    """Print clickable plain URLs and optional per-route availability results."""

    print()
    separator()
    print(Palette.paint("  OMNIFACTORY  /  NAVIGATION & HEALTH", Palette.CYAN), flush=True)
    separator()
    statuses: dict[str, int | None] = {}
    for name, url in endpoints(port):
        if not check:
            print(f"  {name:<20} {url}", flush=True)
            continue
        code, duration, err = probe(url)
        statuses[url] = code
        if code is not None and 200 <= code < 400:
            badge = Palette.paint(f"{code} OK", Palette.GREEN)
        elif code is not None:
            badge = Palette.paint(f"{code}", Palette.YELLOW)
        else:
            badge = Palette.paint("OFFLINE", Palette.RED)
        print(f"  {name:<20} {url}  [{badge}; {duration:.0f} ms]", flush=True)
        if code is None and err:
            log(f"  └─ {err}", Palette.DIM)
    separator()
    print()
    return statuses


def check_port(port: int) -> bool:
    """Preflight check only; never terminates a process occupying the port."""

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def check_dependencies() -> bool:
    """Run `pip check` in diagnostic mode to detect version conflicts."""

    print()
    separator()
    print(Palette.paint("  ENVIRONMENT / DEPENDENCY DIAGNOSTICS", Palette.CYAN))
    separator()
    for package in ("fastapi", "uvicorn", "starlette", "jinja2", "aiogram", "nicegui"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "not installed"
        log(f"{package:<13} {version}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"pip check unavailable: {exc}", Palette.YELLOW)
        return False

    if result.returncode == 0:
        log("Dependency graph: OK", Palette.GREEN)
    else:
        log("Dependency conflicts detected:", Palette.YELLOW)
        for line in (result.stdout + result.stderr).splitlines()[:20]:
            log("  " + line)
    return result.returncode == 0


def monitor_startup(server: uvicorn.Server, port: int, *,
                    open_browser: bool = False, watchdog: bool = False) -> None:
    """Wait for Uvicorn readiness before checking pages or opening browser.

    Runs in a daemon thread so it never obstructs application startup or
    prevents clean program exit. Avoids modifying server.app or the lifespan.
    """

    while not server.started and not server.should_exit:
        time.sleep(0.10)
    if not server.started:
        return

    log("ASGI server started — checking public routes…", Palette.GREEN)
    result = print_links(port, check=True)
    if result.get(local_base(port) + "/health") == 200:
        log("Health endpoint: ONLINE", Palette.GREEN)
    else:
        log("Health endpoint is not returning 200; review /health route.", Palette.YELLOW)

    if open_browser:
        url = local_base(port) + "/studio"
        try:
            if webbrowser.open(url):
                log(f"Browser opened: {url}", Palette.GREEN)
            else:
                log("Browser launch was declined by OS/browser.", Palette.YELLOW)
        except Exception as exc:
            log(f"Could not launch browser: {exc}", Palette.YELLOW)

    if watchdog:
        previous = result.get(local_base(port) + "/health") == 200
        log("Watchdog active: /health every 60s; reports status changes only.")
        while not server.should_exit:
            time.sleep(60)
            if server.should_exit:
                break
            code, duration, _ = probe(local_base(port) + "/health")
            current = code == 200
            if current != previous:
                state = "RECOVERED" if current else "UNHEALTHY"
                log(f"Health changed: {state} (HTTP {code or 'OFFLINE'}, {duration:.0f}ms)",
                    Palette.GREEN if current else Palette.RED)
            previous = current


def parser() -> argparse.ArgumentParser:
    """Argument parser for everyday development and lightweight diagnostics."""

    cli = argparse.ArgumentParser(description="OmniFactory Python Platform launcher")
    cli.add_argument("--port", type=int, default=None, help="Override PORT (default 8000)")
    cli.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"),
                     help="Bind interface; default 0.0.0.0 for containers")
    cli.add_argument("--check", action="store_true", help="Check running server; don't start it")
    cli.add_argument("--doctor", action="store_true", help="Show versions, pip check and URLs")
    cli.add_argument("--open", action="store_true", help="Open /studio after successful startup")
    cli.add_argument("--watch", action="store_true", help="Watch /health without log spam")
    return cli


def main(argv: list[str] | None = None) -> int:
    """Launch exactly the current `server:app`; do not create a second app."""

    options = parser().parse_args(argv)
    port_env = os.environ.get("PORT", "8000")
    try:
        port = options.port if options.port is not None else int(port_env)
    except ValueError:
        log("PORT must be an integer", Palette.RED)
        return 2
    if not 1 <= port <= 65535:
        log("Port must be between 1 and 65535", Palette.RED)
        return 2

    banner(port, options.host)
    if options.check or options.doctor:
        deps_ok = check_dependencies() if options.doctor else True
        states = print_links(port, check=True)
        up = states.get(local_base(port) + "/health") == 200
        return 0 if up and deps_ok else 1

    # Running from any working directory resolves the same application.
    os.chdir(PROJECT_ROOT)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    if check_port(port):
        log(f"Port {port} already accepts connections. Another server may be running.",
            Palette.YELLOW)
        log(f"Use --check to inspect it, or --port {port + 1 if port < 65535 else port - 1}.")
        return 1

    log("Bootstrapping existing FastAPI application: server:app", Palette.CYAN)
    # Keep the same app import, binding, reload and lifespan behavior as the
    # original launcher; only move to Server to observe startup readiness.
    config = uvicorn.Config("server:app", host=options.host, port=port, reload=False)
    server = uvicorn.Server(config)
    threading.Thread(
        target=monitor_startup,
        args=(server, port),
        kwargs={"open_browser": options.open, "watchdog": options.watch},
        daemon=True,
        name="OmniFactory-StartupDiagnostics",
    ).start()
    try:
        server.run()
    except KeyboardInterrupt:
        # Uvicorn normally handles SIGINT itself; this is a fallback.
        log("Shutdown requested", Palette.YELLOW)
    finally:
        uptime = time.monotonic() - STARTED_AT
        log(f"Platform stopped | session uptime: {uptime:.1f}s", Palette.DIM)
    return 0 if server.started else 1


if __name__ == "__main__":
    raise SystemExit(main())
