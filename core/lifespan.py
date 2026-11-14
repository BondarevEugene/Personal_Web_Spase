# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Core Infrastructure
# FILE: core/lifespan.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# ==============================================================================
#
# PURPOSE
# ------------------------------------------------------------------------------
#
# Управление жизненным циклом FastAPI приложения.
#
# Модуль отвечает за:
#
# • Инициализацию инфраструктуры
# • Проверку готовности системы
# • Инициализацию БД
# • Загрузку реестров
# • Запуск фоновых сервисов
# • Корректное завершение приложения
#
# ------------------------------------------------------------------------------
#
# RESPONSIBILITIES
#
# Startup:
#
#   • Инициализация SQLAlchemy
#   • Проверка Registry
#   • Проверка Templates
#   • Проверка Static
#   • Загрузка конфигурации
#
# Shutdown:
#
#   • Закрытие соединений
#   • Освобождение ресурсов
#   • Логирование остановки
#
# ------------------------------------------------------------------------------
#
# IMPORTED BY
#
# server.py
#
# ------------------------------------------------------------------------------
#
# VERSION
#
# 1.0.0
#
# ==============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.logging import logger
from core.database import initialize_database
from portal.bootstrap import ensure_portal_database, ui_source_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Основной жизненный цикл приложения.

    Здесь НЕ должно быть бизнес-логики.

    Только инициализация инфраструктуры.
    """

    logger.info("=" * 70)
    logger.info("OMNIFACTORY PLATFORM STARTING")
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    logger.info("Initializing database...")

    initialize_database()

    logger.info("Legacy platform database ready (not the customer portal).")
    ensure_portal_database()
    home_path, studio_v3 = ui_source_status()
    logger.info("Root HTML source: %s", home_path)
    if not studio_v3:
        logger.error(
            "Root HTML is not Studio v3. The on-disk index.html is outdated or "
            "modified locally. Do NOT trust HTTP 200 as proof of the correct UI."
        )
    else:
        logger.info("Root HTML Studio v3 fingerprint: OK.")

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    logger.info("Loading module registry...")

    # TODO:
    # registry.load()

    logger.info("Registry integration pending (no registry initialized).")

    # ------------------------------------------------------------------
    # AI Runtime
    # ------------------------------------------------------------------

    logger.info("Preparing AI Runtime...")

    # TODO:
    # orchestrator.initialize()

    logger.info("AI Runtime not initialized (feature pending).")

    # ------------------------------------------------------------------
    # Builder
    # ------------------------------------------------------------------

    logger.info("Preparing Builder Engine...")

    # TODO:
    # builder.initialize()

    logger.info("Builder: validation/export endpoints available; live deploy disabled.")

    logger.info("=" * 70)
    logger.info("SYSTEM READY")
    logger.info("=" * 70)

    yield

    logger.info("=" * 70)
    logger.info("SYSTEM SHUTDOWN")
    logger.info("=" * 70)

    # Здесь позже появятся:
    #
    # orchestrator.shutdown()
    # scheduler.shutdown()
    # close_database()