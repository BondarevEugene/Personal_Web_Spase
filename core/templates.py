# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Core Infrastructure
# FILE: core/templates.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# Централизованная работа с Jinja2.
#
# Все Router используют только функцию render().
# ==============================================================================

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

templates.env.globals["PROJECT_NAME"] = "OMNIFACTORY"
templates.env.globals["VERSION"] = "1.0.0"
templates.env.globals["COMPANY"] = "OmniFactory"


def yes_no(value):
    return "Yes" if value else "No"


templates.env.filters["yes_no"] = yes_no


# ==============================================================================
# COMMON RENDER
# ==============================================================================

def render(request: Request, page: str, **context):
    """
    Единая точка рендеринга HTML.
    """

    context["request"] = request

    return templates.TemplateResponse(
        page,
        context
    )