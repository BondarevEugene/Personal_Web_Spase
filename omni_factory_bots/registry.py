# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /omni_factory_bots/engine/registry.py
# DESCRIPTION: Загрузчик реестра компонентов для движка бота.
# AUTHOR: Eugene Bondarev & Gemini AI Collaborator
# STATUS: Production / Core Engine
# ==============================================================================

import json
import os


class Registry:
    def __init__(self, registry_path: str):
        if not os.path.exists(registry_path):
            raise FileNotFoundError(f"Реестр не найден по пути: {registry_path}")

        with open(registry_path, 'r', encoding='utf-8') as f:
            self.modules = json.load(f)

    def get_module_schema(self, module_id: str):
        """Возвращает параметры (схему) для конкретного модуля."""
        return self.modules.get(module_id)

    def validate_node(self, node_data: dict):
        """Проверяет, существует ли такой модуль в системе."""
        return node_data.get('action_module') in self.modules