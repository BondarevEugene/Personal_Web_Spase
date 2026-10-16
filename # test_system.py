# test_system.py
import sys
import os

# Добавляем текущую директорию в системные пути Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from core.registry import Registry
from engine.orchestrator import Orchestrator


async def run_diagnostics():
    print("◈ [DIAGNOSTIC] Запуск инициализации ядра...")

    # 1. Тест загрузки реестра
    reg = Registry('config/registry.json')
    print(f"✅ Реестр загружен. Модулей: {reg._count_modules()}")

    # 2. Тест Оркестратора
    orch = Orchestrator(reg)
    print("✅ Оркестратор инициализирован.")

    # 3. Эмуляция бота
    bot_id = "test_bot_01"
    orch.active_graphs[bot_id] = {"nodes": {}}  # Пустой граф для теста
    print(f"✅ Инстанс бота '{bot_id}' готов к работе.")

    print("◈ [DIAGNOSTIC] Система в норме.")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())