# /services/bot_factory.py
class BotFactory:
    def __init__(self, registry_instance):
        self.registry = registry_instance

    def generate(self, selected_ids: list) -> str:
        """
        Генерирует исполняемый Python-код на основе выбранных ID модулей.
        """
        # Базовый каркас (Шаблон)
        code = (
            "import asyncio\n"
            "from aiogram import Bot, Dispatcher, types\n"
            "from aiogram.filters import CommandStart\n\n"
            "bot = Bot(token='YOUR_TOKEN')\n"
            "dp = Dispatcher()\n\n"
            "@dp.message(CommandStart())\n"
            "async def command_start_handler(message: types.Message):\n"
            "    await message.answer('OmniFactory Bot Online!')\n\n"
        )

        # Инъекция логики модулей
        for mid in selected_ids:
            schema = self.registry.get_module_schema(mid)
            if schema:
                code += f"\n# --- COMPONENT: {mid.upper()} ---\n"
                # В схеме модуля должно быть поле 'code' с логикой (например, обработчики хендлеров)
                code += schema.get('code', '# No code defined') + "\n"

        code += "\nasync def main(): await dp.start_polling(bot)\n"
        code += "if __name__ == '__main__': asyncio.run(main())\n"
        return code