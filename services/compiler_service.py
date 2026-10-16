# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Compiler Service
# FILE: services/compiler_service.py
# ==============================================================================
#
# AUTHOR:#     Yevhenii Bondariev
#
# ARCHITECT:#     OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# CompilerService является фасадом ядра компилятора.
## Он НЕ содержит бизнес-логики.
## Его задача:
##     REST API
#          │
#          ▼
#   CompilerService
#          │
#          ▼
#      Compiler Core
## ==============================================================================

from __future__ import annotations

from api.schemas import CompileRequest
from core.compiler.compiler import Compiler


class CompilerService:
    """
    Фасад Enterprise Compiler.
    """
    def __init__(self):
        self.compiler = Compiler()

    # --------------------------------------------------------------------------

    def compile(self, request: CompileRequest):
        return self.compiler.compile(request)

    # --------------------------------------------------------------------------

    def validate(self, canvas):
        return self.compiler.validate(canvas)

    # --------------------------------------------------------------------------

    def export(self, runtime):
        return self.compiler.export(runtime)

    # --------------------------------------------------------------------------

    def runtime(self, runtime):
        return self.compiler.runtime(runtime)