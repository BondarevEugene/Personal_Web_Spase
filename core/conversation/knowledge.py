from __future__ import annotations

from uuid import uuid4
from datetime import datetime


class Knowledge:
    """
    Знание системы о пользователе.

    Это НЕ переменная.

    Это вывод.

    Например

    Пользователь интересуется ипотекой.

    Пользователь хочет скидку.

    Пользователь готов купить.

    Пользователь VIP.

    Пользователь уже скачал каталог.
    """

    def __init__(
        self,
        name: str,
        value=None,
        confidence: float = 1.0,
        source: str = "manual",
    ):

        self.id = str(uuid4())

        self.name = name

        self.value = value

        self.confidence = confidence

        self.source = source

        self.created = datetime.utcnow()

        self.updated = datetime.utcnow()

        self.tags = []

    @property
    def is_true(self):

        return bool(self.value)

    def set(self, value):

        self.value = value

        self.updated = datetime.utcnow()

    def add_tag(self, tag: str):

        if tag not in self.tags:

            self.tags.append(tag)

    def to_dict(self):

        return {

            "id": self.id,

            "name": self.name,

            "value": self.value,

            "confidence": self.confidence,

            "source": self.source,

            "tags": self.tags

        }