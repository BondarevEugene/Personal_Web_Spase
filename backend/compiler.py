# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# DESCRIPTION: Компилятор JSON-конфигурации в исполняемый Python код.
# ==============================================================================

import json


def compile_bot(config):
    """
    config: dict — данные из React-фронтенда
    Пример: {"selected_ids": ["rag", "shop"], "system_prompt": "Ты помощник..."}
    """

    # Базовый шаблон бота на aiogram
    code = [
        "import logging",
        "from aiogram import Bot, Dispatcher, types",
        "from aiogram.filters import Command",
        "import asyncio",
        "",
        "logging.basicConfig(level=logging.INFO)",
        f"bot = Bot(token='{config.get('token', 'YOUR_TOKEN')}')",
        "dp = Dispatcher()",
        ""
    ]

    # Добавляем логику AI, если выбран модуль 'rag'
    if 'rag' in config['selected_ids']:
        code.append("# AI LOGIC")
        code.append(f"SYSTEM_PROMPT = \"{config.get('system_prompt', 'Be helpful')}\"")
        code.append("@dp.message()")
        code.append("async def ai_handler(message: types.Message):")
        code.append("    # Здесь будет вызов Gemini API")
        code.append("    await message.answer(f'AI Response based on: {SYSTEM_PROMPT}')")
        code.append("")

    code.append("async def main():")
    code.append("    await dp.start_polling(bot)")
    code.append("")
    code.append("if __name__ == '__main__':")
    code.append("    asyncio.run(main())")

    return "\n".join(code)


# Тестовый запуск
test_config = {
    "selected_ids": ["rag"],
    "system_prompt": "Ты — эксперт по дубовой мебели."
}
print(compile_bot(test_config))