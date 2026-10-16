# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Export Engine
# FILE: core/compiler/exporter.py
# VERSION: 2.0
# STATUS: DEVELOPMENT
#
# AUTHOR:#     Yevhenii Bondariev
#
# ARCHITECT:#     OpenAI GPT-5.5
#
# ------------------------------------------------------------------------------
# DESCRIPTION
# ------------------------------------------------------------------------------
#
# Центральный движок экспорта проекта.
#
# Отвечает за:
#
#     • создание структуры каталогов
#     • генерацию README
#     • генерацию Dockerfile
#     • генерацию requirements.txt
#     • генерацию runtime.json
#     • генерацию manifest.json
#     • генерацию .env.example
#     • генерацию .gitignore
#     • создание ZIP
#
# ==============================================================================

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


class Exporter:

    # --------------------------------------------------------------------------

    def export(self, project_path: Path):
        project_path.mkdir(parents=True, exist_ok=True)
        self.create_structure(project_path)
        self.create_readme(project_path)
        self.create_requirements(project_path)
        self.create_dockerfile(project_path)
        self.create_runtime(project_path)
        self.create_manifest(project_path)
        self.create_env(project_path)
        self.create_gitignore(project_path)
        return {
            "success": True,
            "project": str(project_path)
        }

    # --------------------------------------------------------------------------

    def create_structure(self, root: Path):
        folders = [
            "app",
            "api",
            "routers",
            "core",
            "services",
            "config",
            "templates",
            "static",
            "workspace",
            "logs",
            "tests"
        ]

        for folder in folders:
            (root / folder).mkdir(
                parents=True,
                exist_ok=True
            )

    # --------------------------------------------------------------------------

    def create_readme(self, root: Path):
        (root / "README.md").write_text(
f"""# OMNIFACTORY PROJECT

Generated: {datetime.utcnow()}
---

This project was generated automatically.
Platform:
OMNIFACTORY Enterprise Builder

""",
            encoding="utf-8"
        )

    # --------------------------------------------------------------------------

    def create_requirements(self, root: Path):
        requirements = """
fastapi
uvicorn
jinja2
python-dotenv
sqlalchemy
"""

        (root / "requirements.txt").write_text(
            requirements.strip(),
            encoding="utf-8"
        )

    # --------------------------------------------------------------------------

    def create_dockerfile(self, root: Path):
        docker = """
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python","server.py"]
"""

        (root / "Dockerfile").write_text(
            docker.strip(),
            encoding="utf-8"
        )

    # --------------------------------------------------------------------------

    def create_runtime(self, root: Path):
        runtime = {
            "platform": "OMNIFACTORY",
            "version": "2.0",
            "python": "3.12",
            "created": datetime.utcnow().isoformat()
        }
        with open(
            root / "runtime.json",
            "w",
            encoding="utf-8"
        ) as fp:
            json.dump(
                runtime,
                fp,
                indent=4,
                ensure_ascii=False
            )

    # --------------------------------------------------------------------------

    def create_manifest(self, root: Path):
        manifest = {
            "name": "OMNIFACTORY",
            "type": "Builder Project",
            "version": "2.0"
        }
        with open(
            root / "manifest.json",
            "w",
            encoding="utf-8"
        ) as fp:
            json.dump(
                manifest,
                fp,
                indent=4,
                ensure_ascii=False
            )

    # --------------------------------------------------------------------------

    def create_env(self, root: Path):
        env = """
TOKEN=
OPENAI_API_KEY=
DATABASE_URL=
"""
        (root / ".env.example").write_text(
            env.strip(),
            encoding="utf-8"
        )
    # --------------------------------------------------------------------------

    def create_gitignore(self, root: Path):
        ignore = """
__pycache__/
*.pyc
.env
.idea/
.vscode/
venv/
.venv/
"""

        (root / ".gitignore").write_text(
            ignore.strip(),
            encoding="utf-8"
        )
    # --------------------------------------------------------------------------

    def create_zip(self, project_path: Path):
        archive = shutil.make_archive(
            str(project_path),
            "zip",
            project_path
        )

        return archive
