# ==============================================================================
# PROJECT: OMNIFACTORY EVO // CONNECTOR_INTERFACE
# LOCATION: /modules/base.py
# DESCRIPTION: Базовий контракт для всіх месенджерів.
# AUTHOR: Eugene Bondarev
# ==============================================================================
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    async def send_message(self, chat_id: str, text: str, image_url: str = None, buttons: list = None):
        """Універсальний метод відправки"""
        pass