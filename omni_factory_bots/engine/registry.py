# ==============================================================================
# PROJECT: OMNIFACTORY // EVO_CORE
# LOCATION: /omni_factory_bots/engine/registry.py
# DESCRIPTION: Улучшенный гидратор реестра с валидацией и логированием.
# ==============================================================================

import json
import os
import logging

# Настройка логирования для отслеживания загрузки компонентов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegistryEngine")

class Registry:
    def __init__(self, registry_path: str = 'config/registry.json'):
        """Инициализация реестра с автоматическим поиском конфига."""
        self.modules = {}
        # Вычисляем корень проекта (Personal_Web_Spase)
        # Учитывая, что мы в omni_factory_bots/engine/, поднимаемся на 2 уровня
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.abs_path = os.path.join(base_dir, registry_path)

        self._load_registry()

    def _load_registry(self):
        """Безопасная загрузка и парсинг JSON."""
        if not os.path.exists(self.abs_path):
            logger.error(f"Файл реестра отсутствует: {self.abs_path}")
            raise FileNotFoundError(f"Файл реестра не найден: {self.abs_path}")

        try:
            with open(self.abs_path, 'r', encoding='utf-8') as f:
                self.modules = json.load(f)
            logger.info(f"Реестр успешно инициализирован. Загружено модулей: {self._count_modules()}")
        except json.JSONDecodeError as e:
            logger.critical(f"Ошибка синтаксиса в registry.json: {e}")
            raise ValueError(f"Некорректный формат JSON в реестре: {e}")

    def _count_modules(self) -> int:
        """Вспомогательный метод для подсчета общего количества модулей."""
        return sum(len(cat) for cat in self.modules.values() if isinstance(cat, list))

    def get_module_schema(self, module_id: str) -> dict:
        """Поиск схемы модуля по ID."""
        for category, modules in self.modules.items():
            for module in modules:
                if module.get('id') == module_id:
                    return module
        logger.warning(f"Модуль с ID '{module_id}' не найден в реестре.")
        return None

    def get_modules_by_category(self, category_name: str) -> list:
        """Возвращает все модули указанной категории (CORE, CRM, AI и т.д.)."""
        return self.modules.get(category_name, [])

    def list_all_ids(self) -> list:
        """Возвращает плоский список всех доступных ID модулей."""
        return [mod['id'] for cat in self.modules.values() for mod in cat]