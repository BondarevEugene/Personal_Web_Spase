# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Enterprise Compiler
# FILE: core/compiler/compiler.py
# VERSION: 2.0 Enterprise
# ==============================================================================
#
# DESCRIPTION
# ------------------------------------------------------------------------------
#
# Центральный Compiler платформы.
# Compiler НЕ содержит логики FastAPI.
# Compiler НЕ знает про Swagger.
# Compiler НЕ знает про Builder UI.
# Compiler работает только с:
#     ProjectModel
#     CompilerContext
# Pipeline:
#     Request
#         │
#         ▼
#     Context
#         │
#         ▼
#     Validation
#         │
#         ▼
#     Registry
#         │
#         ▼
#     Resolve Modules
#         │
#         ▼
#     Workspace
#         │
#         ▼
#     Project Generator
#         │
#         ▼
#     Export
#         │
#         ▼
#     Archive
#         │
#         ▼
#     Result
#
# ==============================================================================

from __future__ import annotations

import logging
from pathlib import Path

from core.project import ProjectModel
from core.compiler.context import CompilerContext

from services.project_generator import ProjectGenerator
from services.module_manager import ModuleManager

from core.compiler.exporter import Exporter

logger = logging.getLogger(__name__)


class Compiler:
    """
    Центральный Compiler платформы.
    """
    # ----------------------------------------------------------------------

    def __init__(
        self,
        generator: ProjectGenerator | None = None,
        exporter: Exporter | None = None,
        module_manager: ModuleManager | None = None
    ):
        self.generator = generator or ProjectGenerator()
        self.exporter = exporter or Exporter()
        self.module_manager = module_manager or ModuleManager()

    # ----------------------------------------------------------------------

    def compile(
        self,
        request
    ) -> CompilerContext:
        """
        Полный цикл сборки проекта.
        """
        logger.info("Compiler started.")
        context = self._prepare_context(request)
        self._validate_request(context)
        self._load_registry(context)
        self._resolve_modules(context)
        self._prepare_workspace(context)
        self._generate_project(context)
        self._export_project(context)
        self._archive_project(context)
        self._finish(context)
        logger.info("Compiler finished.")
        return context

    # ----------------------------------------------------------------------

    def _prepare_context(self, request) -> CompilerContext:
        """
        Создание CompilerContext.
        """
        context = CompilerContext()
        context.request = request
        project = ProjectModel()
        project.name = request.project_name
        project.runtime = request.runtime
        project.target = request.target
        context.project = project
        logger.info(
            "Context prepared. Project=%s",
            project.name
        )
        return context
    # ----------------------------------------------------------------------
    # VALIDATION
    # ----------------------------------------------------------------------

    def _validate_request(self, context: CompilerContext) -> None:
        """
        Первичная проверка CompileRequest.
        Здесь проверяется только корректность входных данных.
        Логическая проверка схемы Builder выполняется Validator.
        """
        logger.info("Validation started.")
        request = context.request
        if request is None:
            context.add_error("CompileRequest is None.")
            return
        if not getattr(request, "project_name", None):
            context.add_error("Project name is required.")
        if not getattr(request, "runtime", None):
            context.add_error("Runtime is required.")
        if not getattr(request, "target", None):
            context.add_error("Target is required.")
        if context.errors:
            logger.error(
                "Validation failed (%s errors).",
                len(context.errors)
            )
            return
        logger.info("Validation completed successfully.")

    # ----------------------------------------------------------------------
    # REGISTRY
    # ----------------------------------------------------------------------

    def _load_registry(self, context: CompilerContext) -> None:
        """
        Загружает registry.json через ModuleManager.
        """
        logger.info("Loading registry...")
        try:
            registry = self.module_manager.load_registry()
            context.registry = registry
            logger.info(
                "Registry loaded (%s modules).",
                len(registry)
            )
        except Exception as ex:
            context.add_error(str(ex))
            logger.exception(ex)

    # ----------------------------------------------------------------------
    # MODULE RESOLUTION
    # ----------------------------------------------------------------------

    def _resolve_modules(self, context: CompilerContext) -> None:
        """
        Преобразует список выбранных пользователем модулей
        в реальные описания модулей Registry.
        """
        logger.info("Resolving modules...")
        if not context.valid:
            return
        request = context.request
        selected = getattr(
            request,
            "selected_nodes",
            []
        )
        context.selected_modules = selected
        project = context.project
        registry = context.registry
        resolved = []
        #
        # registry может быть:
        #
        # {
        #     "modules": [...]
        # }
        #
        # либо уже списком.
        #

        if isinstance(registry, dict):
            registry_modules = registry.get(
                "modules",
                []
            )
        else:
            registry_modules = registry
        for module_name in selected:
            module = next(
                (
                    item
                    for item in registry_modules
                    if item.get("name") == module_name
                ),
                None
            )
            if module is None:
                context.add_warning(
                    f"Module '{module_name}' not found."
                )
                continue
            resolved.append(module)
            project.add_module(module)
        context.resolved_modules = resolved
        logger.info(
            "Resolved %s modules.",
            len(resolved)
        )
        context.update_statistics(
            "modules",
            len(resolved)
        )
    # ----------------------------------------------------------------------
    # WORKSPACE
    # ----------------------------------------------------------------------

    def _prepare_workspace(
        self,
        context: CompilerContext
    ) -> None:
        """
        Подготавливает рабочую директорию сборки.

        Структура создается ProjectGenerator,
        Compiler только сохраняет путь.
        """
        logger.info("Preparing workspace...")
        if not context.valid:
            return
        workspace = self.generator.prepare_workspace(
            context.project
        )
        context.set_workspace(workspace)
        logger.info(
            "Workspace prepared: %s",
            workspace
        )

    # ----------------------------------------------------------------------
    # PROJECT GENERATION
    # ----------------------------------------------------------------------

    def _generate_project(self, context: CompilerContext) -> None:
        """
        Генерация проекта.
        Здесь создаются:
            • app/
            • api/
            • routers/
            • templates/
            • static/
            • README
            • Dockerfile
            • requirements
        """
        logger.info("Generating project...")
        if not context.valid:
            return
        project = context.project
        workspace = context.workspace
        generated = self.generator.generate(
            project=project,
            workspace=workspace
        )
        #
        # generated может быть:
        #
        # ProjectModel
        #
        # dict
        #
        # list
        #

        if isinstance(generated, dict):
            for file in generated.get(
                "files",
                []
            ):
                context.add_file(file)
            for directory in generated.get(
                "directories",
                []
            ):
                context.add_directory(directory)
        logger.info(
            "Project generation completed."
        )

    # ----------------------------------------------------------------------
    # EXPORT
    # ----------------------------------------------------------------------

    def _export_project(self, context: CompilerContext) -> None:
        """
        Экспорт проекта.
        Exporter создает:
            README
            Dockerfile
            requirements
            runtime.json
            manifest.json
            .gitignore
            .env.example
        """
        logger.info(
            "Export started."
        )
        if not context.valid:
            return
        result = self.exporter.export(
            context.workspace
        )
        if isinstance(result, dict):
            for key, value in result.items():
                context.metadata[key] = value
        logger.info(
            "Export completed."
        )

    # ----------------------------------------------------------------------
    # ARCHIVE
    # ----------------------------------------------------------------------

    def _archive_project(self, context: CompilerContext) -> None:
        """
        Создание ZIP архива.
        """
        logger.info(
            "Creating archive..."
        )
        if not context.valid:
            return
        archive = self.exporter.create_zip(
            context.workspace
        )
        context.set_archive(
            Path(archive)
        )
        logger.info(
            "Archive created: %s",
            archive
        )
    # ----------------------------------------------------------------------
    # FINISH
    # ----------------------------------------------------------------------

    def _finish(
        self,
        context: CompilerContext
    ) -> CompilerContext:
        """
        Финализация процесса компиляции.

        Подсчитывает статистику и формирует
        итоговое состояние CompilerContext.
        """

        logger.info("Finalizing compilation...")

        context.update_statistics(
            "generated_modules",
            len(context.project.modules)
        )

        context.update_statistics(
            "generated_files",
            len(context.generated_files)
        )

        context.update_statistics(
            "generated_directories",
            len(context.generated_directories)
        )

        context.update_statistics(
            "warnings",
            len(context.warnings)
        )

        context.update_statistics(
            "errors",
            len(context.errors)
        )

        context.metadata["compiler"] = "OMNIFACTORY Enterprise Compiler"

        context.metadata["compiler_version"] = "2.0"

        context.metadata["success"] = context.valid

        logger.info(
            "Compilation finished. Success=%s",
            context.valid
        )

        return context

    # ----------------------------------------------------------------------
    # PUBLIC RESULT
    # ----------------------------------------------------------------------

    def compile_result(self, context: CompilerContext) -> dict:
        """
        Возвращает публичный результат компиляции.
        Этот метод используется Builder API.
        Внутренние объекты Compiler наружу
        не передаются.
        """

        return {
            "success": context.valid,
            "build_id": context.build_id,
            "runtime_id": context.runtime_id,
            "project": {
                "id": context.project.id,
                "name": context.project.name,
                "runtime": context.project.runtime,
                "target": context.project.target,
                "modules": len(context.project.modules),
                "components": len(context.project.components),
            },

            "workspace": (
                str(context.workspace)
                if context.workspace
                else None
            ),

            "archive": (
                str(context.archive)
                if context.archive
                else None
            ),
            "statistics": context.statistics,
            "warnings": context.warnings,
            "errors": context.errors,
            "metadata": context.metadata
        }

    # ----------------------------------------------------------------------
    # CLEANUP
    # ----------------------------------------------------------------------

    def cleanup(self, context: CompilerContext) -> None:
        """
        Очистка временных ресурсов.
        Пока метод оставлен пустым.
        В будущем здесь будут:
            • удаление временных файлов
            • очистка Runtime Cache
            • закрытие соединений
            • очистка очередей
        """
        logger.info("Cleanup completed.")

    # ----------------------------------------------------------------------
    # VERSION
    # ----------------------------------------------------------------------

    @property
    def version(self) -> str:
        """
        Версия Compiler.
        """
        return "2.0 Enterprise"

    # ----------------------------------------------------------------------
    # NAME
    # ----------------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Имя Compiler.
        """
        return "OMNIFACTORY Enterprise Compiler"
