"""
Conversation Intelligence Engine

Главное ядро всей платформы OmniFactory.

Здесь не должно быть ничего,
что связано с Telegram,
WhatsApp,
Viber,
Discord,
FastAPI,
или Compiler.

Это полностью независимый язык
описания диалогов.

Любой Runtime должен работать
через эти модели.
"""

from .conversation import Conversation
from .journey import Journey
from .scene import Scene
from .decision import Decision
from .action import Action
from .attachment import Attachment
from .form import Form
from .field import Field
from .memory import Memory
from .variable import Variable