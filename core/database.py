
# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Core Infrastructure
# FILE: core/database.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE:
# Централизованный модуль работы с базой данных.
#
# RESPONSIBILITIES:
# • Инициализация SQLAlchemy Engine
# • Создание SessionLocal
# • Объявление Base
# • Dependency get_db()
# • Создание таблиц
#
# DEPENDENCIES:
# SQLAlchemy
#
# IMPORTED BY:
# server.py
# routes/*
# services/*
#
# VERSION: 1.0.0
# ==============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_URL

# ==============================================================================
# SQLAlchemy Engine
# ==============================================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# ==============================================================================
# Session Factory
# ==============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ==============================================================================
# Declarative Base
# ==============================================================================

Base = declarative_base()

# ==============================================================================
# Dependency
# ==============================================================================

def get_db():
    """
    FastAPI dependency.

    Создает новую сессию SQLAlchemy
    для каждого HTTP-запроса.

    После завершения запроса
    соединение автоматически закрывается.
    """

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ==============================================================================
# Database Initialization
# ==============================================================================

def initialize_database():
    """
    Создает отсутствующие таблицы.

    Вызывается один раз
    при старте приложения.
    """

    Base.metadata.create_all(bind=engine)


# 2. ИНИЦИАЛИЗАЦИЯ БД (может потом ужалить???)
from core.config import DATABASE_URL

engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)