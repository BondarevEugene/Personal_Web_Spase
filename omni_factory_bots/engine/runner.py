# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /omni_factory_bots/engine/runner.py
# DESCRIPTION: Ядро-интерпретатор. Выполняет логику на основе JSON-графа.
# AUTHOR: Eugene Bondarev & Gemini AI Collaborator
# STATUS: Production / Core Engine
# ==============================================================================
import importlib
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class BotRunner:
    def __init__(self, registry):
        self.registry = registry
        logging.basicConfig(level=logging.INFO)

    def build_keyboard(self, buttons_data):
        """
        Преобразует JSON-список кнопок из билдера в клавиатуру aiogram
        buttons_data: [{"text": "Текст", "callback": "action_id"}, ...]
        """
        builder = InlineKeyboardBuilder()
        for btn in buttons_data:
            builder.button(text=btn['text'], callback_data=btn['callback'])
        return builder.as_markup()

    async def execute_node(self, node, context):
        """
        node: узел из JSON-графа
        context: словарь с данными (message, state, user_id)
        """
        config = node.get("data", {}).get("config", {})
        module_id = node.get("name")  # В Drawflow это имя ноды

        # 1. Логика для "Rich Message" (коммуникация)
        if module_id == "tg_message_pro":
            text = config.get("text", "...")
            buttons = config.get("buttons", [])
            reply_markup = self.build_keyboard(buttons) if buttons else None

            await context['message'].answer(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return {"status": "sent"}

        # 2. Старая логика динамических модулей
        try:
            module = importlib.import_module(f"modules.{module_id}")
            return await module.run(context, config)
        except ImportError:
            logging.error(f"Модуль {module_id} не найден!")
            return {"error": "Module not found"}

    def get_next_step(self, node, choice=None):
        """Возвращает ID следующего узла по логике графа"""
        # Здесь должна быть логика поиска выхода в Drawflow JSON
        return node.get("outputs", {}).get("out_1", {}).get("connections", [{}])[0].get("node")