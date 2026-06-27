# ==============================================================================
# PROJECT: OMNIFACTORY EVO // BRIDGE_LAYER
# LOCATION: /modules/factory_bridge.py
# DESCRIPTION: Адаптер для интеграции старых модулей в новую архитектуру.
# ==============================================================================
from services.bot_factory import MODULES_REGISTRY


class FactoryBridge:
    @staticmethod
    def get_module_logic(module_id):
        """
        Берет код из старого BotFactory и возвращает его как исполняемую задачу.
        """
        module_data = MODULES_REGISTRY.get(module_id)
        if not module_data:
            return None

        # Здесь мы возвращаем функцию-обертку, которая выполнит твой старый код
        return module_data.get('code')

    @staticmethod
    def get_connector(messenger_type):
        """Возвращает нужный класс коннектора для передачи сообщений."""
        connectors = {
            "telegram": "TelegramConnector",
            "viber": "ViberConnector"
        }
        return connectors.get(messenger_type)

    # Адаптер: берет описание модуля и превращает его в команду для Оркестратора
    class FactoryBridge:
        @staticmethod
        def execute(module_id, params, context):
            # 1. Берем код из твоего рабочего bot_factory.py
            logic = MODULES_REGISTRY[module_id]['code']

            # 2. Выполняем (например, через exec или вызов функции)
            # В идеале: запускаем как асинхронную задачу внутри контекста бота
            return run_logic(logic, params, context)