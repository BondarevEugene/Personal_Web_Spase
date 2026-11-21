# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: API Response Models
# FILE: api/responses.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# Унифицированные ответы API.
#
# НИКАКИХ return {}
#
# Все API платформы должны использовать единый формат ответа.
#
# ==============================================================================

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ==============================================================================
# BASE RESPONSE
# ==============================================================================

class ApiResponse(BaseModel):

    success: bool = Field(
        default=True,
        description="Статус выполнения операции."
    )

    message: str = Field(
        default="Operation completed successfully.",
        description="Описание результата."
    )

    version: str = Field(
        default="2.0.0",
        description="Версия API."
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC время формирования ответа."
    )

    data: Any = Field(
        default=None,
        description="Полезная нагрузка."
    )


# ==============================================================================
# ERROR RESPONSE
# ==============================================================================

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
