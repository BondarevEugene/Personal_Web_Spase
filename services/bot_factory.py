# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /services/bot_factory.py
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Ядро генерации кода Telegram-ботов.
# PURPOSE: Сборка финального .py файла на основе выбранных ID модулей.
# DEPENDENCIES: jinja2, bot_modules registry
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

class BotFactory:
    def __init__(self, selected_ids: list):
        self.selected_ids = selected_ids
        self.code_blocks = {
            "welcome": """
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать в наш сервис!", reply_markup=main_menu)
""",
            "voice_to_text": """
@dp.message(F.voice)
async def handle_voice(message: Message):
    text = await speech_to_text(message.voice)
    await message.answer(f"Вы сказали: {text}")
""",
            "pay_stars": """
@dp.message(Command("pay"))
async def create_invoice(message: Message):
    await message.answer_invoice(title="Оплата", payload="order_1", currency="XTR", prices=[...])
"""
            # Сюда добавляются шаблоны для всех 50+ модулей
        }

    def generate(self) -> str:
        # 1. Формируем импорты
        header = "import asyncio\nfrom aiogram import Bot, Dispatcher, F\nfrom aiogram.filters import CommandStart\n\n"

        # 2. Инициализация
        init = "bot = Bot(token='YOUR_TOKEN')\ndp = Dispatcher()\n\n"

        # 3. Сборка модулей
        body = ""
        for mid in self.selected_ids:
            if mid in self.code_blocks:
                body += self.code_blocks[mid] + "\n"

        # 4. Footer
        footer = ("\nasync def main():\n    await dp.start_polling(bot)\n\nif __name__ == '__main__':\n    "
                  "asyncio.run(main())")

        return header + init + body + footer