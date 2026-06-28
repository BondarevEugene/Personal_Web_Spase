# connectors/telegram_connector.py
from omni_factory_bots.modules.base import BaseConnector

class TelegramConnector(BaseConnector):
    def __init__(self, token: str):
        self.token = token
        print(f"DEBUG: TelegramConnector инициализирован с токеном {token[:5]}...")

    async def send_message(self, chat_id: str, text: str, image_url: str = None, buttons: list = None):
        # Здесь будет реальный вызов Aiogram или любого API
        print(f"PROD_LOG: Telegram -> {chat_id} | Text: {text}")
        return True