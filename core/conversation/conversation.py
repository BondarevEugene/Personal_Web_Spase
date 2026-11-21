# ==============================================================================
# OMNIFACTORY
# Conversation Intelligence Engine (CIE)
# ------------------------------------------------------------------------------
# FILE:
#     core/conversation/conversation.py
#
# DESCRIPTION:
# ------------------------------------------------------------------------------
# Главный объект всей платформы.
#
# Conversation — это НЕ Telegram Bot.
#
# Conversation — это универсальная модель цифрового общения.
#
# Именно она потом может быть опубликована как:
#
# • Telegram Bot
# • WhatsApp Bot
# • Viber Bot
# • Discord Bot
# • Instagram Bot
# • Web Chat
# • Mobile App
# • Voice Assistant
#
# Все Runtime работают с одним Conversation.
#
# ------------------------------------------------------------------------------
#
# Внутри Conversation находятся:
#
#     Journeys
#         ↓
#     Graph
#         ↓
#     Scenes
#         ↓
#     Decisions
#         ↓
#     Actions
#
# ------------------------------------------------------------------------------
#
# Conversation НИЧЕГО не знает
# о Telegram.
#
# Conversation НЕ знает
# о FastAPI.
#
# Conversation НЕ знает
# о HTML.
#
# Это полностью независимый движок.
#
# ==============================================================================
from __future__ import annotations

from uuid import uuid4
from datetime import datetime

from .journey import Journey
from .exceptions import (
    DuplicateJourney,
    JourneyNotFound,
)
class Conversation:
    """
    Главная сущность всей платформы.

    Один проект == одна Conversation.

    Например

    Интернет-магазин

    или

    Банк

    или

    Медицинский помощник

    или

    HR Assistant

    Все это Conversation.
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        language: str = "ru",
    ):

        # -------------------------------------------------
        # Основная информация
        # -------------------------------------------------

        self.id = str(uuid4())

        self.title = title

        self.description = description

        self.language = language

        self.created = datetime.utcnow()

        self.updated = datetime.utcnow()

        self.version = 1

        self.author = ""

        self.company = ""

        self.tags = []

        # -------------------------------------------------
        # Основное содержимое
        # -------------------------------------------------

        self.journeys: dict[str, Journey] = {}

        # -------------------------------------------------
        # Общие переменные проекта
        # -------------------------------------------------

        self.variables = {}

        # -------------------------------------------------
        # Метаданные
        # -------------------------------------------------

        self.metadata = {}

        # -------------------------------------------------
        # Аналитика
        # -------------------------------------------------

        self.analytics = {

            "users": 0,

            "sessions": 0,

            "completed": 0,

            "drop": 0

        }

        # =====================================================================
        # JOURNEYS
        # =====================================================================

        def add_journey(self, journey: Journey):
            """
            Добавить Journey.

            Один Conversation
            может содержать
            несколько независимых
            пользовательских сценариев.

            Например

            Продажа

            Поддержка

            FAQ

            VIP

            Администрирование
            """

            if journey.id in self.journeys:
                raise DuplicateJourney(journey.title)

            self.journeys[journey.id] = journey

            return journey

        def remove_journey(self, journey_id: str):

            """
            Удаление Journey.
            """

            if journey_id not in self.journeys:
                raise JourneyNotFound(journey_id)

            del self.journeys[journey_id]

            def journey(self, journey_id: str):

                """
                Получить Journey.
                """

                if journey_id not in self.journeys:
                    raise JourneyNotFound(journey_id)

                return self.journeys[journey_id]

            def find_journey_by_title(self, title: str):

                """
                Поиск Journey
                по названию.
                """

                for journey in self.journeys.values():

                    if journey.title == title:
                        return journey

                return None

            # =====================================================================
            # STATISTICS
            # =====================================================================

            @property
            def scene_count(self):

                total = 0

                for journey in self.journeys.values():
                    total += len(journey.scenes)

                return total

            @property
            def decision_count(self):

                total = 0

                for journey in self.journeys.values():
                    total += journey.decision_count

                return total

            @property
            def transition_count(self):

                total = 0

                for journey in self.journeys.values():
                    total += journey.transition_count

                return total
    # =====================================================================
    # VALIDATION
    # =====================================================================

    def validate(self):

        """
        Полная проверка проекта.

        Builder будет вызывать
        этот метод постоянно.

        Именно здесь позже появятся:

        ✔ поиск циклов

        ✔ тупиков

        ✔ пустых сцен

        ✔ отсутствующих переходов

        ✔ недостижимых сцен

        ✔ AI-анализ
        """

        report = []

        if len(self.journeys) == 0:

            report.append(

                "Conversation has no journeys."

            )

        for journey in self.journeys.values():

            report.extend(

                journey.validate()

            )

        return report
    # =====================================================================
    # SERIALIZATION
    # =====================================================================

    def to_dict(self):

        return {

            "id": self.id,

            "title": self.title,

            "description": self.description,

            "language": self.language,

            "version": self.version,

            "journeys": [

                j.to_dict()

                for j in self.journeys.values()

            ]

        }
