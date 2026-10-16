# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Core Infrastructure
# FILE: core/static.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# Подключение статических ресурсов проекта.
# Единственная точка регистрации StaticFiles.
# ==============================================================================

from pathlib import Path
from fastapi.staticfiles import StaticFiles
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def mount_static(app):
    static_dir = PROJECT_ROOT / "static"
    if static_dir.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(static_dir)),
            name="static"
        )
