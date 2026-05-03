# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /models.py
# VERSION: 1.2.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Определение моделей данных Pydantic.
# PURPOSE: Валидация структур для коммуникаций и заказов.
# DEPENDENCIES: None
# AUTHORS: Human & AI Collaboration
# STATUS: Beta
# ==============================================================================


from pydantic import BaseModel
from typing import List, Optional, Dict


class CommunicationLog(BaseModel):
    id: str
    timestamp: str
    client_name: str
    summary: str
    sentiment: str  # Positive, Neutral, Questioning
    extracted_entities: Dict[str, str]  # {"item": "Oak Table", "delivery": "Urgent"}
    status: str  # New, In Progress, Concluded


class UserSkill(BaseModel):
    name: str
    level: str  # например: "Junior", "Middle", "Senior"


class UserProfile(BaseModel):
    uid: str
    username: str
    skills: List[UserSkill] = []


class CRMEvent(db.Model):
    __tablename__ = 'crm_events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    target_site = db.Column(db.String(100))  # К какому сайту привязано (напр. Genesys)
    linked_script = db.Column(db.String(100))  # ID скрипта для автозапуска
    status = db.Column(db.String(20), default="PENDING")  # PENDING, EXECUTED, FAILED


"""
--------------------------------------------------------------------------------
PROJECT: WebFactory | Intelligence Systems
MODULE:  Database Models (models.py)
VERSION: 1.0.1
DESCRIPTION:
    Определение структуры данных для CRM-системы и планировщика задач.
    Обеспечивает хранение событий, расписаний и связей с внешними узлами.
--------------------------------------------------------------------------------
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Инициализация объекта БД без привязки к приложению (инкапсуляция)
db = SQLAlchemy()


class CRMEvent(db.Model):
    """Модель события для календаря и планировщика задач[cite: 12]."""
    __tablename__ = 'crm_events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # Название (напр. "Backup Genesys")
    description = db.Column(db.Text)  # Описание задачи
    scheduled_time = db.Column(db.DateTime, nullable=False)  # Время запуска

    # Связь с конкретным сайтом/узлом под управлением
    target_site = db.Column(db.String(100), default="LOCAL")

    # ID или путь к скрипту, который должен выполниться (напр. "scan_links")
    linked_script = db.Column(db.String(100))

    # Статус выполнения: PENDING (ожидание), EXECUTED (выполнено), FAILED (ошибка)
    status = db.Column(db.String(20), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Преобразование в JSON для календаря на фронтенде."""
        return {
            'id': self.id,
            'title': self.title,
            'start': self.scheduled_time.isoformat(),
            'description': self.description,
            'status': self.status
        }


class ManagedSite(db.Model):
    """Реестр сайтов, находящихся под управлением CRM[cite: 13]."""
    __tablename__ = 'managed_sites'

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(150), unique=True, nullable=False)
    api_key = db.Column(db.String(100))  # Секретный ключ для моста (Secret Handshake)
    last_sync = db.Column(db.DateTime)
