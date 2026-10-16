from __future__ import annotations

from abc import ABC, abstractmethod


class BaseBlock(ABC):
    """
    Базовый класс любого блока конструктора.
    Каждый блок обязан реализовать compile().
    """

    id = "base"
    name = "Base Block"
    category = "core"
    version = "1.0"

    # ---------------------------------------------

    @abstractmethod
    def compile(self, context) -> str:
        """
        Возвращает Python код,
        который будет вставлен в проект.
        """
        pass

    # ---------------------------------------------

    def imports(self) -> list[str]:
        return []

    # ---------------------------------------------

    def requirements(self) -> list[str]:
        return []

    # ---------------------------------------------

    def validate(self):
        return []

    # ---------------------------------------------

    def description(self):
        return ""

    # ---------------------------------------------

    def metadata(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "version": self.version
        }
