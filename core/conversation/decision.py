from __future__ import annotations

from uuid import uuid4


class Decision:
    """
    Decision

    Не просто кнопка.

    А решение пользователя.

    Например

    Купить

    Узнать подробнее

    Получить консультацию

    Скачать PDF
    """

    def __init__(
        self,
        caption: str,
        target_scene: str,
        icon: str = "",
        priority: int = 100,
        weight: float = 1.0,
    ):

        self.id = str(uuid4())

        self.caption = caption

        self.target_scene = target_scene

        self.icon = icon

        self.priority = priority

        self.weight = weight

        self.condition = None

        self.actions = []

        self.analytics = {
            "clicks": 0,
            "success": 0,
            "fails": 0
        }

    def clicked(self):

        self.analytics["clicks"] += 1

    def success(self):

        self.analytics["success"] += 1

    def fail(self):

        self.analytics["fails"] += 1

    @property
    def conversion(self):

        if self.analytics["clicks"] == 0:
            return 0

        return round(
            self.analytics["success"]
            /
            self.analytics["clicks"]
            *
            100,
            2,
        )

    def add_action(self, action):

        self.actions.append(action)

    def to_dict(self):

        return {

            "id": self.id,

            "caption": self.caption,

            "target_scene": self.target_scene,

            "priority": self.priority,

            "weight": self.weight,

            "conversion": self.conversion,

            "actions": [
                a.to_dict()
                for a in self.actions
            ]
        }