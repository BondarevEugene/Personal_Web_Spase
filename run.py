# ==============================================================================
# PROJECT: OMNIFACTORY EVO // SYSTEM_BOOTSTRAPPER (⚡ REBOOT & FIXED 2026 ⚡)
# LOCATION: /run.py
# PURPOSE: Single entry point with strict health checks and clean termination
# ==============================================================================
import os
import sys
import subprocess
import time
import logging

# 1. Исправляем пути ДО любых импортов локальных модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Добавляем родительскую директорию на случай, если структура требует этого
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(1, parent_dir)

# Передаем правильный PYTHONPATH в переменные окружения для подпроцессов
os.environ["PYTHONPATH"] = current_dir + os.pathsep + parent_dir + os.pathsep + os.environ.get("PYTHONPATH", "")

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("SystemBootstrapper")


def check_environment():
    """Проверка директории фронтенда"""
    absolute_frontend_path = r"C:\Users\bonda\PycharmProjects\Personal_Web_Spase\frontend"
    if os.path.exists(absolute_frontend_path) and os.path.isdir(absolute_frontend_path):
        logger.info(f"✅ Директория фронтенда успешно подключена: {absolute_frontend_path}")
        return absolute_frontend_path
    logger.error(f"❌ Фронтенд не найден по абсолютному пути: {absolute_frontend_path}")
    sys.exit(1)


def start_backend():
    """Запуск FastAPI ядра без shell=True (чтобы не плодить зомби-процессы на Windows)"""
    logger.info("📡 Запуск асинхронного Python FastAPI ядра...")

    # Запускаем напрямую через sys.executable (python.exe) как модуль uvicorn
    # Убираем shell=True, чтобы была возможность чисто убить процесс по PID
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8088"],
        cwd=current_dir,
        env=os.environ
    )
    return backend_process


def start_frontend(frontend_dir):
    """Запуск Vite Dev Server"""
    logger.info("⚛️ Запуск интерфейса оператора Vite Dev Server...")
    # Для npm на Windows shell=True необходим, так как npm — это .cmd файл
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )
    return frontend_process


def print_routes():
    """Безопасный вывод роутов ПОСЛЕ настройки окружения"""
    try:
        import server
        logger.info("=" * 80)
        logger.info("REGISTERED API CONTRACT ENDPOINTS:")
        for route in server.app.routes:
            methods = ",".join(route.methods) if hasattr(route, "methods") else "INTERNAL"
            logger.info(f"   [{methods}] -> http://127.0.0.1:8088{route.path}")
        logger.info("=" * 80)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось прочитать карту роутов напрямую: {str(e)}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   OMNIFACTORY EVO // SYSTEM AUTOMATION                                       ║
║──────────────────────────────────────────────────────────────────────────────║
║ MODULE      : Application Launcher & Cluster Supervisor                      ║
║ FILE        : run.py                                                         ║
║ PURPOSE     : Single entry point for the entire platform (Vite + FastAPI)   ║
║ STATUS      : STANDBY -> ACTIVATING                                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    frontend_dir = check_environment()

    backend_proc = None
    frontend_proc = None

    try:
        # 1. Запуск и валидация Бэкенда
        backend_proc = start_backend()

        # Ждем 2.5 секунды, давая Uvicorn подгрузить модули (включая engine)
        time.sleep(2.5)

        # ЖЕСТКАЯ ПРОВЕРКА: Если процесс бэкенда завершился (вернул код), значит он упал
        if backend_proc.poll() is not None:
            logger.error("❌ Критическая ошибка: Python ядро упало при запуске! Развертывание прервано.")
            sys.exit(1)

        # Если бэкенд выжил — безопасно выводим роуты в консоль
        print_routes()

        # 2. Запуск Фронтенда
        frontend_proc = start_frontend(frontend_dir)
        time.sleep(1.5)

        logger.info("🚀 Кластер OmniFactory успешно развернут.")
        logger.info("👉 Документация API (Swagger): http://127.0.0.1:8088/docs")
        logger.info("👉 Панель управления (Vite)  : http://localhost:5173/ (или следующий свободный порт)")
        logger.info("Нажмите CTRL+C для одновременной остановки всех процессов.")

        # Мониторинг работы обоих процессов в реальном времени
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                logger.error("❌ Бэкенд неожиданно прекратил работу!")
                break
            if frontend_proc.poll() is not None:
                logger.error("❌ Фронтенд неожиданно прекратил работу!")
                break

    except KeyboardInterrupt:
        logger.warning("\n🛑 [SIGINT] Получен сигнал остановки. Сворачивание кластера...")
    finally:
        # Корректное и жесткое уничтожение процессов для Windows без зависших портов
        if backend_proc:
            try:
                backend_proc.terminate()
                backend_proc.wait(timeout=2)
            except Exception:
                backend_proc.kill()

        if frontend_proc:
            try:
                # Так как Vite запускался через shell=True, на Windows используем taskkill для очистки дерева процессов
                if os.name == 'nt':
                    subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                else:
                    frontend_proc.terminate()
            except Exception:
                pass

        logger.info("💀 Все сервисы успешно остановлены. Порты свободны.")


if __name__ == "__main__":
    main()