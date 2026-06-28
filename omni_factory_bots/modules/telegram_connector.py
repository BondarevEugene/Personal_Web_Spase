# ==============================================================================
# PROJECT: OMNIFACTORY EVO // TELEGRAM_CONNECTOR
# LOCATION: /modules/telegram_connector.py
# ==============================================================================
from .base import BaseConnector

class TelegramConnector(BaseConnector):
    def __init__(self, token: str):
        self.token = token
        # Тут ініціалізація твого клієнта Aiogram (bot = Bot(token=token))

    async def send_message(self, chat_id: str, text: str, image_url: str = None, buttons: list = None):
        # Тут реальна логіка відправки
        if image_url:
            print(f"[TG_SEND] Отправка фото {image_url} в {chat_id}")
        else:
            print(f"[TG_SEND] Отправка текста '{text}' в {chat_id}")