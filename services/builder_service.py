# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Builder Service
# FILE: services/builder_service.py
# ==============================================================================
#
# PURPOSE
# ------------------------------------------------------------------------------
# Главный сервис Builder.
# Используется:
# • REST API
# • Web Builder
# • Desktop Builder
# • Telegram Builder
# • CLI
#
# ==============================================================================

from services.compiler_service import CompilerService
from services.module_manager import ModuleManager
from services.project_generator import ProjectGenerator


class BuilderService:

    def __init__(self):
        self.compiler = CompilerService()
        self.registry = ModuleManager()
        self.generator = ProjectGenerator()

    # --------------------------------------------------------------------------
    def get_registry(self):
        return self.registry.get_registry()

    # --------------------------------------------------------------------------
    def get_modules(self):
        return self.registry.get_all_modules()

    # --------------------------------------------------------------------------

    def compile(self, request):
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

    # --------------------------------------------------------------------------

    def generate(self, request):
        """
        Пока используется существующий ProjectGenerator.
        Позже будет заменен новым Enterprise Compiler.
        """
        return self.generator.generate(request)
