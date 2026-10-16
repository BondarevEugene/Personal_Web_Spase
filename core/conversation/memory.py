from __future__ import annotations

from .knowledge import Knowledge


class Memory:
    """
    Память конкретного пользователя.

    НЕ AI Memory.

    А память сценария.

    Именно здесь хранится

    что пользователь уже видел,

    скачал,

    ответил,

    купил.
    """

    def __init__(self):

        self.variables = {}

        self.knowledge = {}

        self.history = []

    # ----------------------------

    def set_variable(self, name, value):

        self.variables[name] = value

    # ----------------------------

    def variable(self, name, default=None):

        return self.variables.get(name, default)

    # ----------------------------

    def add_knowledge(self, knowledge: Knowledge):

        self.knowledge[knowledge.name] = knowledge

    # ----------------------------

    def knows(self, name):

        return name in self.knowledge

    # ----------------------------

    def knowledge_value(self, name):

        if name not in self.knowledge:

            return None

        return self.knowledge[name].value

    # ----------------------------

    def visit(self, scene_id):

        self.history.append(scene_id)

    # ----------------------------

    def visited(self, scene_id):

        return scene_id in self.history

    # ----------------------------

    def reset(self):

        self.variables.clear()

        self.knowledge.clear()

        self.history.clear()