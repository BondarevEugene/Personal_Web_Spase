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
import operator


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


async def route(self, bot_id, user_id, event, state):
    # 1. Получаем текущий узел пользователя из Redis (через StateManager)
    current_node_id = await state.get_current_node(user_id)
    graph = orchestrator.active_graphs[bot_id]

    # 2. Находим текущий узел в JSON-графе
    node = graph['nodes'][current_node_id]

    # 3. Выполняем узел
    result = await self.execute_node(node, event)

    # 4. Переходим к следующему шагу
    next_node = self.get_next_step(node, event.data)
    await state.set_current_node(user_id, next_node)


def get_next_step(self, node, choice=None):
    connections = self.graph['links']  # Ваши линки из JSON
    # Если роутер вернул путь, ищем линк с нужным class (true_path/false_path)
    for link in connections:
        if link['output_node'] == node['id'] and link['output_class'] == choice:
            return link['input_node']
    return None


async def execute_router(self, node, context):
    config = node.get("data", {}).get("config", {})

    # Данные для проверки
    val = context.get('user_data', {}).get(config.get("field_to_check"))
    target = float(config.get("value"))  # Приводим к типу
    op_str = config.get("operator")  # '>', '<', '==', '>='

    # Безопасный словарь операций
    ops = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq
    }

    try:
        val = float(val)  # Приведение типов для сравнения
        is_true = ops[op_str](val, target)
    except Exception as e:
        logging.error(f"Ошибка логики роутера: {e}")
        is_true = False  # По умолчанию идем в false_path при ошибке

    return "true_path" if is_true else "false_path"


import importlib
import logging
import operator


class BotRunner:
    def __init__(self, graph):
        self.graph = graph

    async def execute_node(self, node, context):
        """
        node: узел из JSON-графа
        context: словарь с данными (message, state, user_id, db)
        """
        config = node.get("data", {}).get("config", {})
        module_id = node.get("name")

        # 1. Коммуникационный узел (Текст/Кнопки)
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

        # 2. Логический роутер (Бинарное ветвление)
        elif module_id == "binary_router":
            return await self.execute_router(node, context)

        # 3. Динамические модули (CRM, AI и т.д.)
        else:
            try:
                module = importlib.import_module(f"modules.{module_id}")
                # Предполагаем, что у модуля есть класс, например CRMModule
                # Для простоты вызываем метод run модуля
                return await module.run(context, config)
            except ImportError:
                logging.error(f"Модуль {module_id} не найден по пути modules.{module_id}!")
                return {"error": "Module not found"}

    async def execute_router(self, node, context):
        """Логика бинарной развилки"""
        config = node.get("data", {}).get("config", {})
        val = context.get('user_data', {}).get(config.get("field_to_check"))
        target = float(config.get("value", 0))
        op_str = config.get("operator", "==")

        ops = {">": operator.gt, "<": operator.lt, "==": operator.eq}

        try:
            is_true = ops[op_str](float(val), target)
        except:
            is_true = False

        return "true_path" if is_true else "false_path"

    def build_keyboard(self, buttons):
        # Реализация клавиатуры (заглушка или ваш код)
        pass