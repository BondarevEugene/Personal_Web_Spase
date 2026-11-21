"""Diagnostics for what FastAPI app and routes are ACTUALLY running.

Read-only: no migrations, no secrets, no network provider actions.
Run: python -m scripts.portal_doctor --port 8001
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def inspect_code():
    from server import app
    from routers import home
    print("Python executable :", sys.executable)
    print("Imported server   :", Path(sys.modules["server"].__file__).resolve())
    print("Home router       :", Path(home.__file__).resolve())
    print("Route count       :", len(app.routes))
    paths = {getattr(route, "path", "") for route in app.routes}
    for path in ("/", "/architect", "/bots/lab", "/health", "/openapi.json",
                 "/studio-assets"):
        print(f"  {path:24} {'registered' if path in paths else 'NOT REGISTERED'}")
    try:
        schema = app.openapi()
        print("OpenAPI generation: OK", len(schema.get("paths", {})), "paths")
    except Exception:
        print("OpenAPI generation: FAILED")
        traceback.print_exc()
        return False
    return True


def inspect_server(port: int):
    print("Running server    :", f"http://127.0.0.1:{port}")
    for path in ("/health", "/bots/lab", "/openapi.json", "/studio-assets/graph_workspace.css"):
        try:
            with urlopen(Request(f"http://127.0.0.1:{port}{path}",
                                 headers={"User-Agent": "OmniFactory-Portal-Doctor"}),
                         timeout=3) as response:
                data = response.read(512)
                status = response.status
        except HTTPError as exc:
            status = exc.code
            data = exc.read(512)
        except (URLError, TimeoutError, OSError) as exc:
            print(f"  {path:35} offline ({type(exc).__name__})")
            continue
        print(f"  {path:35} HTTP {status} {data[:180]!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    opts = parser.parse_args()
    good = inspect_code()
    inspect_server(opts.port)
    if not good:
        sys.exit(1)


if __name__ == "__main__":
    main()
