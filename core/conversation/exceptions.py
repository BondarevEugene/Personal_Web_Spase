"""
Conversation Engine Exceptions
"""


class ConversationException(Exception):
    """Базовая ошибка движка."""


class ValidationException(ConversationException):
    """Ошибка проверки."""


class SceneNotFound(ConversationException):
    """Сцена отсутствует."""


class JourneyNotFound(ConversationException):
    """Journey отсутствует."""


class DecisionNotFound(ConversationException):
    """Decision отсутствует."""


class DuplicateScene(ConversationException):
    """Сцена уже существует."""


class DuplicateJourney(ConversationException):
    """Journey уже существует."""


class InvalidTransition(ConversationException):
    """Некорректный переход."""


class InvalidAction(ConversationException):
    """Некорректное действие."""