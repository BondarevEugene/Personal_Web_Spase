from __future__ import annotations

from uuid import uuid4

from .attachment import Attachment
from .decision import Decision
from .enums import Emotion
from .enums import ScenePurpose
from .enums import SceneType


class Scene:
    """
    Главный строительный блок Conversation.

    НЕ Node.

    НЕ Message.

    А полноценная сцена общения.
    """

    def __init__(
            self,
            title: str,
            purpose: ScenePurpose,
            scene_type: SceneType = SceneType.NORMAL,
    ):

        self.id = str(uuid4())

        self.title = title

        self.scene_type = scene_type

        self.purpose = purpose

        self.description = ""

        self.message = ""

        self.subtitle = ""

        self.notes = ""

        self.emotion = Emotion.NEUTRAL

        self.attachments: list[Attachment] = []

        self.decisions: list[Decision] = []

        self.transitions = []

        self.actions = []

        self.variables = []

        self.tags = []

        self.objectives = []

        #
        # KPI
        #

        self.goal = ""

        self.expected_result = ""

        #
        # Analytics
        #

        self.analytics = {

            "views": 0,

            "completed": 0,

            "failed": 0,

            "exit": 0,

            "avg_time": 0,

        }

        self.conditions = []

    # ------------------------------------------------
    def add_condition(self, fn):
        self.conditions.append(fn)

    # ------------------------------------------------

    def set_message(self, text: str):

        self.message = text

        return self

    # ------------------------------------------------

    def add_attachment(self, attachment: Attachment):

        self.attachments.append(attachment)

        return attachment

    # ------------------------------------------------

    def add_decision(self, decision: Decision):

        self.decisions.append(decision)

        return decision

    # ------------------------------------------------

    def add_action(self, action):

        self.actions.append(action)

    # ------------------------------------------------

    def viewed(self):

        self.analytics["views"] += 1

    # ------------------------------------------------

    def completed(self):

        self.analytics["completed"] += 1

    # ------------------------------------------------

    def failed(self):

        self.analytics["failed"] += 1

    # ------------------------------------------------

    @property
    def conversion(self):

        if self.analytics["views"] == 0:
            return 0

        return round(

            self.analytics["completed"]

            /

            self.analytics["views"]

            *

            100,

            2

        )

    # ------------------------------------------------

    @property
    def score(self):
        """
        Интегральная оценка сцены.

        Позже сюда подключится AI.
        """

        score = 100

        if len(self.decisions) == 0:
            score -= 30

        if len(self.message) < 5:
            score -= 15

        if self.analytics["exit"] > 100:
            score -= 25

        return max(score, 0)

    # ------------------------------------------------

    def validate(self):

        errors = []

        if self.title == "":
            errors.append("Scene title is empty")

        if self.message == "":
            errors.append("Scene message is empty")

        return errors

    # ------------------------------------------------

    def to_dict(self):

        return {

            "id": self.id,

            "title": self.title,

            "purpose": self.purpose.value,

            "scene_type": self.scene_type.value,

            "message": self.message,

            "emotion": self.emotion.value,

            "goal": self.goal,

            "expected_result": self.expected_result,

            "score": self.score,

            "conversion": self.conversion,

            "attachments": [

                a.to_dict()

                for a in self.attachments

            ],

            "transitions": [

                t.to_dict()

                for t in self.transitions

            ],

            "decisions": [

                d.to_dict()

                for d in self.decisions
            ]

        }

    def add_transition(self, transition):
        self.transitions.append(transition)
        return transition

    def add_objective(self, objective):
        self.objectives.append(objective)
        return objective

    def available(self, memory):

        """
        Может ли пользователь увидеть
        эту сцену.
        """

        if not hasattr(self, "conditions"):
            return True

        for condition in self.conditions:

            if not condition(memory):
                return False

        return True
