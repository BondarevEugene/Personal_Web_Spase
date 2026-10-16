from uuid import uuid4


class Objective:
    """
    Бизнес-цель сцены.

    Именно по ней считается эффективность.
    """

    def __init__(

        self,

        title: str,

        description: str = ""

    ):

        self.id = str(uuid4())

        self.title = title

        self.description = description

        self.completed = False

        self.weight = 100

        self.analytics = {

            "success": 0,

            "failed": 0

        }

    def success(self):

        self.completed = True

        self.analytics["success"] += 1

    def fail(self):

        self.analytics["failed"] += 1

    @property
    def conversion(self):

        total = (

            self.analytics["success"]

            +

            self.analytics["failed"]

        )

        if total == 0:

            return 0

        return round(

            self.analytics["success"]

            /

            total

            *

            100,

            2

        )

    def to_dict(self):

        return {

            "id": self.id,

            "title": self.title,

            "description": self.description,

            "completed": self.completed,

            "conversion": self.conversion

        }