# -*- coding: utf-8 -*-
# ==============================================================================
# PROJECT: OMNIFACTORY EVO // SYSTEM NODE: BOT COMPONENT FACTORY
# REVISION: v11.0.0 // GEN-oS RUNTIME COMPLIANCE SPECIFICATION
# LOCATION: /services/component_factory.py
# PURPOSE: Factual mapping of visual UI canvas elements into executable Python/Aiogram code
# ==============================================================================

from __future__ import annotations
import json
from typing import Dict, Any, List


class BotComponentLibrary:
    """
    Индустриальная библиотека компонентов OmniFactory.
    Хранит шаблоны питоновского кода и компилирует JSON-ноды холста в асинхронные хэндлеры.
    """

    def __init__(self):
        # Глобальный реестр канонических шаблонов для aiogram 3.x
        self.templates = {
            # 1. Простой текстовый ответ
            "text_response": (
                "    # --- COMPONENT: TEXT RESPONSE ---\n"
                "    await message.answer(\n"
                "        text=\"{text}\",\n"
                "        parse_mode=\"Markdown\"\n"
                "    )\n"
            ),

            # 2. Вопрос с кнопками (Инлайн-диалог)
            "inline_dialog": (
                "    # --- COMPONENT: INLINE DIALOG ---\n"
                "    builder = InlineKeyboardBuilder()\n"
                "    buttons_data = {buttons_list}\n"
                "    for btn in buttons_data:\n"
                "        builder.button(text=btn['text'], callback_data=btn['callback'])\n"
                "    builder.adjust({adjust_value})\n"
                "    await message.answer(\n"
                "        text=\"{question_text}\",\n"
                "        reply_markup=builder.as_markup(),\n"
                "        parse_mode=\"Markdown\"\n"
                "    )\n"
            ),

            # 3. Переключатель состояний (FSM State Router)
            "fsm_state_setter": (
                "    # --- COMPONENT: FSM STATE SETTER ---\n"
                "    await state.set_state(CustomBotStates.{state_name})\n"
                "    await message.answer(\n"
                "        text=\"{prompt_text}\",\n"
                "        reply_markup=types.ReplyKeyboardRemove()\n"
                "    )\n"
            ),

            # 4. Отправка медиа-ресурса (Универсальный Media Router)
            "media_sender": (
                "    # --- COMPONENT: MEDIA SENDER ---\n"
                "    file_path = \"{file_path}\"\n"
                "    caption = \"{caption}\"\n"
                "    if os.path.exists(file_path):\n"
                "        input_file = types.FSInputFile(file_path)\n"
                "        if \"{media_type}\" == \"photo\":\n"
                "            await message.answer_photo(photo=input_file, caption=caption)\n"
                "        elif \"{media_type}\" == \"document\":\n"
                "            await message.answer_document(document=input_file, caption=caption)\n"
                "        elif \"{media_type}\" == \"voice\":\n"
                "            await message.answer_voice(voice=input_file, caption=caption)\n"
                "    else:\n"
                "        await message.answer(f\"⚠️ Ошибка: Файл по пути {{file_path}} не найден в системе.\")\n"
            ),

            # 5. Приём и валидация файла (Входной шлюз)
            "file_receiver": (
                "    # --- COMPONENT: FILE RECEIVER ---\n"
                "    if message.document:\n"
                "        document = message.document\n"
                "        target_dir = \"{target_directory}\"\n"
                "        os.makedirs(target_dir, exist_ok=True)\n"
                "        file_info = await bot.get_file(document.file_id)\n"
                "        await bot.download_file(file_info.file_path, os.path.join(target_dir, document.file_name))\n"
                "        await message.answer(f\"✓ Документ {{document.file_name}} успешно принят и сохранен.\")\n"
                "    else:\n"
                "        await message.answer(\"❌ Ошибка: Ожидался файл формата 'document'. Пожалуйста, повторите отправку.\")\n"
            ),

            # 6. Когнитивный ИИ-блок (Нейросетевой хаб Ollama/CodeLlama)
            "ai_cognitive_hub": (
                "    # --- COMPONENT: AI COGNITIVE HUB ---\n"
                "    system_context = \"{system_prompt}\"\n"
                "    user_input = message.text if message.text else \"[Медиа-контент]\"\n"
                "    try:\n"
                "        loop = asyncio.get_event_loop()\n"
                "        response = await loop.run_in_executor(\n"
                "            None,\n"
                "            lambda: ollama.chat(\n"
                "                model=\"{model_name}\",\n"
                "                messages=[\n"
                "                    {{\"role\": \"system\", \"content\": system_context}},\n"
                "                    {{\"role\": \"user\", \"content\": user_input}}\n"
                "                ]\n"
                "            )\n"
                "        )\n"
                "        await message.answer(response['message']['content'])\n"
                "    except Exception as e:\n"
                "        await message.answer(f\"🤖 [ИИ-Нода]: Ошибка инференса модели: {{str(e)}}\")\n"
            )
        }

    def compile_node(self, node_type: str, data: Dict[str, Any]) -> str:
        """
        Парсит внутренние параметры графической ноды и подставляет их в питоновский шаблон.
        """
        template = self.templates.get(node_type)
        if not template:
            return f"    # ⚠️ Компонент [{node_type}] не зарегистрирован в ядре OmniFactory.\n"

        try:
            if node_type == "text_response":
                return template.format(text=data.get("text", "Приветственная директива OmniFactory Evo."))

            elif node_type == "inline_dialog":
                # Обработка списка кнопок. Если пуст — генерируем базовую структуру
                raw_buttons = data.get("buttons", "Узнать больше|info_cb;Связаться|contact_cb")
                buttons_list = []
                for pair in raw_buttons.split(";"):
                    if "|" in pair:
                        t, c = pair.split("|")
                        buttons_list.append({"text": t.strip(), "callback": c.strip()})

                return template.format(
                    buttons_list=repr(buttons_list),
                    adjust_value=int(data.get("adjust", 2)),
                    question_text=data.get("question", "Выберите опцию на панели:")
                )

            elif node_type == "fsm_state_setter":
                return template.format(
                    state_name=data.get("state_name", "WAITING_FOR_INPUT"),
                    prompt_text=data.get("prompt", "Система переведена в режим ожидания ввода. Введите данные:")
                )

            elif node_type == "media_sender":
                return template.format(
                    file_path=data.get("file_path", "storage/manifest.json"),
                    caption=data.get("caption", "Файл выгружен из репозитория хоста."),
                    media_type=data.get("media_type", "document")
                )

            elif node_type == "file_receiver":
                return template.format(target_directory=data.get("target_dir", "downloads/"))

            elif node_type == "ai_cognitive_hub":
                return template.format(
                    system_prompt=data.get("system_prompt", "Ты — автономный бот. Отвечай коротко и строго по делу."),
                    model_name=data.get("model", "codellama")
                )

        except Exception as e:
            return f"    # ❌ Ошибка компиляции параметров ноды {node_type}: {str(e)}\n"

        return ""

    def compile_canvas_flow(self, drawflow_export: Dict[str, Any]) -> str:
        """
        Оркеструет весь граф Drawflow. Перебирает все ноды холста и собирает их код воедино.
        """
        python_handlers = []
        home_module = drawflow_export.get("drawflow", {}).get("Home", {})
        nodes = home_module.get("data", {})

        if not nodes:
            return "    await message.answer(\"🤖 Сценарий пуст. Пожалуйста, добавьте компоненты на холст.\")"

        for node_id, node_meta in nodes.items():
            node_type = node_meta.get("name")
            node_data = node_meta.get("data", {})

            python_handlers.append(f"    # --- START_NODE_ID: {node_id} ---")
            python_handlers.append(self.compile_node(node_type, node_data))
            python_handlers.append(f"    # --- END_NODE_ID: {node_id} ---\n")

        return "\n".join(python_handlers)

    def __repr__(self):
        return f"<BotComponentLibrary: {len(self.templates)} канонических Python-модулей>"


# Экспорт синглтона
component_library = BotComponentLibrary()