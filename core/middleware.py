# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Core Infrastructure
# FILE: core/middleware.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
#
# Централизованная регистрация Middleware.
#
# Любое Middleware подключается исключительно
# через setup_middleware().
#
# ==============================================================================
#

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


def setup_middleware(app):

    # ==========================================================
    # CORS
    # ==========================================================

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==========================================================
    # GZIP
    # ==========================================================

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1024
    )