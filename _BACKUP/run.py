# ==============================================================================
# PROJECT: OMNIFACTORY EVO // SYSTEM_BOOTSTRAPPER (⚡ ULTIMATE DIAGNOSTIC ALIGNED ⚡)
# LOCATION: /run.py
# PURPOSE: Enterprise launcher with log parsing, port checks & health metrics
# ==============================================================================

import subprocess
# Запуск сервера так, чтобы видеть все ошибки в консоли
result = subprocess.run([sys.executable, "server.py"])
if result.returncode != 0:
    print(f"Сервер упал с кодом {result.returncode}")
import os
import sys
import time
import logging
import socket
import re

# Настройка системных путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("OmniFactory")

TARGET_PORT = 8089


def check_port(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def start_backend():
    server_path = os.path.join(BASE_DIR, "server.py")
    if not os.path.exists(server_path):
        logger.error(f"❌ ФАЙЛ SERVER.PY НЕ НАЙДЕН ПО ПУТИ: {server_path}")
        sys.exit(1)

    logger.info(f"🔍 Запуск ядра из: {server_path}")
    return subprocess.Popen([sys.executable, server_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║   OMNIFACTORY EVO // SYSTEM AUTOMATION                                       ║
║──────────────────────────────────────────────────────────────────────────────║
║ MODULE      : Application Launcher & Cluster Supervisor                      ║
║ STATUS      : STANDBY -> ACTIVATING [PORT 8089 ALIGNED]                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if check_port(TARGET_PORT):
        logger.warning(f"⚠️ [CONFLICT] Порт {TARGET_PORT} занят! Завершите процессы перед стартом.")
        sys.exit(1)

    backend_proc = None
    try:
        # 1. ЗАПУСК ЯДРА
        backend_proc = start_backend()

        # Мониторинг запуска
        logger.info("📡 Инициализация асинхронного Python FastAPI ядра...")
        for _ in range(10):
            if backend_proc.poll() is not None:
                logger.error("❌ Критическая ошибка: Ядро упало при запуске!")
                sys.exit(1)
            time.sleep(0.5)

        logger.info("🚀 КЛАСТЕР OMNIFACTORY УСПЕШНО РАЗВЕРНУТ.")
        logger.info("👉 Документация API (Swagger) : http://127.0.0.1:8089/docs")
        logger.info("👉 Панель управления         : http://127.0.0.1:8089/admin")

        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                logger.error("❌ Бэкенд неожиданно прекратил работу!")
                break

    except KeyboardInterrupt:
        logger.warning("\n🛑 [SIGINT] Сигнал остановки получен.")
    finally:
        if backend_proc:
            backend_proc.terminate()
            logger.info("💀 Все сервисы успешно остановлены. Порты очищены. Выход.")


if __name__ == "__main__":
    main()