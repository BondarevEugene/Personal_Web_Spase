# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Module Manager
# FILE: services/module_manager.py
# ==============================================================================
#
# Единая точка доступа к Registry платформы.
#
# Отвечает за:
#   • загрузку registry.json
#   • поиск модулей
#   • категории
#   • статистику
#   • обновление Registry
#
# ==============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ModuleManager:

    def __init__(self, registry_path: str | None = None):

        if registry_path is None:

            registry_path = (
                Path(__file__).resolve().parent.parent
                / "omni_factory_bots"
                / "config"
                / "registry.json"
            )

        self.registry_path = Path(registry_path)

        self.registry: dict[str, Any] = {}

        self.reload()

    # --------------------------------------------------------------------------

    def reload(self):

        if not self.registry_path.exists():

            self.registry = {}

            return

        with open(
            self.registry_path,
            "r",
            encoding="utf-8"
        ) as fp:

            self.registry = json.load(fp)

    # --------------------------------------------------------------------------

    def get_registry(self):

        return self.registry

    # --------------------------------------------------------------------------

    def get_all_modules(self):

        modules = []

        categories = self.registry.get("categories", {})

        for category_name, category in categories.items():

            for module in category.get("modules", []):

                module["category"] = category_name

                modules.append(module)

        return modules

    # --------------------------------------------------------------------------

    def get_module(self, module_id: str):

        for module in self.get_all_modules():

            if module.get("id") == module_id:

                return module

        return None

    # --------------------------------------------------------------------------

    def get_categories(self):

        return list(self.registry.get("categories", {}).keys())

    # --------------------------------------------------------------------------

    def statistics(self):

        modules = self.get_all_modules()

        return {

            "modules": len(modules),

            "categories": len(self.get_categories()),

            "enabled": len(
                [
                    m
                    for m in modules
                    if m.get("enabled", True)
                ]
            )

        }
