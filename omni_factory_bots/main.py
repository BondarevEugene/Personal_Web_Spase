# ==============================================================================
# PROJECT: OMNIFACTORY EVO // SYSTEM_ENTRY_POINT
# LOCATION: /main.py
# DESCRIPTION: Главный диспетчер. Инициализация коннекторов и запуск Оркестратора.
# ==============================================================================
import asyncio
from engine.runner import BotRunner
from engine.orchestrator import Orchestrator
from connectors.telegram_connector import TelegramConnector


# Предполагаем, что ты создашь этот файл (см. ниже)

async def main():
    # 1. Инициализация ядра (Hub)
    orchestrator = Orchestrator()

    # 2. Настройка бота (Администрирование)
    # Это можно вынести в отдельный конфиг JSON, но для теста делаем тут
    bot_id = "coffee_bot_01"
    config = {
        "messenger_type": "telegram",
        "token": "ВАШ_ТОКЕН_ИЗ_BOTFATHER"
    }

    # 3. Регистрация коннектора (Spoke)
    # Orchestrator сам создаст TelegramConnector внутри себя
    orchestrator.load_bot_config(bot_id, config)

    print(">>> OMNIFACTORY SYSTEM ONLINE")
    print(">>> TELEMETRY: Hub initialized. Connectors active.")

    # 4. Эмуляция события (сюда потом придет реальный Webhook от Telegram)
    # Допустим, пришло сообщение от пользователя
    await orchestrator.route_event(
        bot_id=bot_id,
        chat_id="user_123",
        node_data={
            "content": {"text": "Привет! Как дела?"},
            "type": "message"
        }
    )


async def main():
    runner = BotRunner('data/bot.json')

    # Эмулируем работу бота
    print("--- ЗАПУСК БОТА ---")
    current_node = "start"

    # 1. Получаем стартовое сообщение
    response = await runner.execute(current_node)
    print(f"Бот: {response['content']}")
    print(f"Варианты: {[s['text'] for s in response['next_steps']]}")

    # 2. Эмулируем выбор пользователя (например, клик на "Инфо")
    current_node = "info_node"
    response = await runner.execute(current_node)
    print(f"\nБот: {response['content']}")


if __name__ == "__main__":
    asyncio.run(main())