from __future__ import annotations

from uuid import uuid4
from datetime import datetime


class Transition:
    """
    Интеллектуальный переход между двумя сценами.

    Это НЕ стрелка.

    Это полноценный объект аналитики.
    """

    def __init__(
        self,
        source_scene: str,
        target_scene: str,
        decision_id: str | None = None,
    ):

        self.id = str(uuid4())

        self.source_scene = source_scene

        self.target_scene = target_scene

        self.decision_id = decision_id

        #
        # Логика
        #

        self.enabled = True

        self.priority = 100

        self.weight = 1.0

        self.condition = None

        self.variables = {}

        #
        # A/B Testing
        #

        self.experiment = None

        self.variant = "A"

        #
        # AI
        #

        self.ai_enabled = False

        self.ai_comment = ""

        self.ai_score = 100

        #
        # Analytics
        #

        self.analytics = {

            "created": datetime.utcnow(),

            "passed": 0,

            "failed": 0,

            "avg_time": 0,

            "drop": 0

        }

    # ------------------------------------------------

    def passed(self):

        self.analytics["passed"] += 1

    # ------------------------------------------------

    def failed(self):

        self.analytics["failed"] += 1

    # ------------------------------------------------

    @property
    def conversion(self):

        total = self.analytics["passed"] + self.analytics["failed"]

        if total == 0:

            return 0

        return round(

            self.analytics["passed"]

            /

            total

            *

            100,

            2

        )

    # ------------------------------------------------

    @property
    def score(self):

        score = 100

        if self.analytics["drop"] > 50:

            score -= 30

        if self.analytics["failed"] > self.analytics["passed"]:

            score -= 20

        return max(score, 0)

    # ------------------------------------------------

    def to_dict(self):

        return {

            "id": self.id,

            "source": self.source_scene,

            "target": self.target_scene,

            "decision": self.decision_id,

            "priority": self.priority,

            "weight": self.weight,

            "conversion": self.conversion,

            "score": self.score,

            "ai_score": self.ai_score,

            "ai_comment": self.ai_comment,

            "enabled": self.enabled

        }