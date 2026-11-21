"""Railway production release contracts: no silent return to the legacy server."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docker_runs_current_platform_and_respects_railway_port():
    docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "python:3.12-slim" in docker
    assert "uvicorn server:app" in docker
    assert "0.0.0.0" in docker
    assert "${PORT:-8080}" in docker
    assert "gunicorn" not in docker
    assert "run.py" not in docker


def test_railway_health_gate_is_configured():
    config = json.loads((ROOT / "railway.json").read_text(encoding="utf-8"))
    assert config["build"]["builder"] == "DOCKERFILE"
    assert config["deploy"]["healthcheckPath"] == "/health"
    assert config["deploy"]["restartPolicyType"] == "ON_FAILURE"


def test_current_platform_exposes_health_and_new_home():
    server = (ROOT / "server.py").read_text(encoding="utf-8")
    home = (ROOT / "routers/home.py").read_text(encoding="utf-8")
    assert '@app.get("/health"' in server
    assert 'from routers.home import router as home_router' in server
    assert 'BASE_DIR / "index.html"' in home
    assert "studio-v3-platform" in home


def test_release_instructions_require_staging_and_rollback():
    instructions = (ROOT / "docs/RAILWAY_PLATFORM_RELEASE.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "staging", "Neon", "alembic", "/health",
        "/account", "/architect", "/automation/studio", "rollback",
    ):
        assert token in instructions
