# ==============================================================================
# PROJECT: OMNIFACTORY EVO // SYSTEM_BOOTSTRAPPER (⚡ ULTIMATE DIAGNOSTIC ⚡)
# LOCATION: /run.py
# PURPOSE: Enterprise launcher with log parsing, port checks & health metrics
# ==============================================================================
import os
import sys
import subprocess
import time
import logging
import socket
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("OmniFactory")


def check_port(port, host="127.0.0.1"):
    """Проверка, занят ли порт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def check_environment():
    """Глубокая диагностика инфраструктуры перед запуском"""
    logger.info("🔍 ТЕСТИРОВАНИЕ ИНФРАСТРУКТУРЫ...")

    # 1. Проверка фронтенда
    absolute_frontend_path = r"C:\Users\bonda\PycharmProjects\Personal_Web_Spase\frontend"
    if not (os.path.exists(absolute_frontend_path) and os.path.isdir(absolute_frontend_path)):
        logger.error(f"❌ Критическая ошибка: Фронтенд отсутствует по пути: {absolute_frontend_path}")
        sys.exit(1)
    logger.info(f"🧬 [STATUS] Фронтенд-контур обнаружен: {absolute_frontend_path}")

    # 2. Проверка критических файлов конфигурации
    registry_path = os.path.join(current_dir, "omni_factory_bots", "config", "registry.json")
    if os.path.exists(registry_path):
        logger.info(f"📦 [STATUS] База конфигураций registry.json: OK ({os.path.getsize(registry_path)} байт)")
    else:
        logger.warning(
            f"⚠️ [WARNING] Файл реестра не найден по пути: {registry_path}. Бэкенд может выдать ошибку инициализации.")

    # 3. Проверка конфликтов портов
    if check_port(8088):
        logger.warning("⚠️ [CONFLICT] Порт бэкенда 8088 уже занят! Возможно, прошлая сессия не была закрыта.")
    else:
        logger.info("📡 [STATUS] Сетевой порт ядра 8088: СВОБОДЕН")

    return absolute_frontend_path


def start_backend():
    logger.info("📡 Инициализация асинхронного Python FastAPI ядра...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8088"],
        cwd=current_dir,
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return backend_process


def start_frontend(frontend_dir):
    logger.info("⚛️ Развертывание интерфейса оператора Vite Dev Server...")
    # Запускаем с перенаправлением вывода, чтобы вытащить реальный порт
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return frontend_process


def print_routes():
    try:
        import server
        logger.info("=" * 80)
        logger.info("🌐 REGISTERED API CONTRACT ENDPOINTS:")
        for route in server.app.routes:
            methods = ",".join(route.methods) if hasattr(route, "methods") else "INTERNAL"
            # Фильтруем системные роуты для чистоты логов
            if not route.path.startswith(("/static", "/openapi", "/json")):
                logger.info(f"   [{methods:<6}] -> http://127.0.0.1:8088{route.path}")
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
        # 1. СТАРТ БЭКЕНДА
        backend_proc = start_backend()
        time.sleep(2.5)

        if backend_proc.poll() is not None:
            logger.error("❌ Критическая ошибка: Python ядро упало при запуске! Развертывание прервано.")
            sys.exit(1)

        print_routes()

        # 2. СТАРТ ФРОНТЕНДА
        frontend_proc = start_frontend(frontend_dir)

        # Интеллектуальный поиск порта Vite в логах
        vite_url = "http://localhost:5173/"  # дефолт, если не распарсим
        logger.info("⏳ Ожидание выделения портов подсистемой Vite...")

        # Читаем первые строки вывода Vite, чтобы узнать точный порт
        for _ in range(30):
            line = frontend_proc.stdout.readline()
            if "Local:" in line or "http://" in line:
                match = re.search(r'http://[^\s]+', line)
                if match:
                    vite_url = match.group(0)
                    break
            if frontend_proc.poll() is not None:
                break

        # 3. ФИНАЛЬНЫЙ СТАТУС ПАКЕТ
        logger.info("🚀 КЛАСТЕР OMNIFACTORY УСПЕШНО РАЗВЕРНУТ В ПАМЯТИ.")
        print("\n" + "═" * 80)
        logger.info(f"👉 Документация API (Swagger) : http://127.0.0.1:8088/docs")
        logger.info(f"👉 Панель управления (Vite)    : {vite_url}")
        logger.info(f"🛠️  Режим супервизора           : АКТИВЕН [Мониторинг процессов...]")
        print("═" * 80 + "\n")
        logger.info("Нажмите CTRL+C для одновременной безопасной остановки кластера.")

        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                logger.error("❌ Бэкенд неожиданно прекратил работу!")
                break
            if frontend_proc.poll() is not None:
                logger.error("❌ Фронтенд неожиданно прекратил работу!")
                break

    except KeyboardInterrupt:
        logger.warning("\n🛑 [SIGINT] Сигнал остановки получен. Инициирована процедура сворачивания...")
    finally:
        if backend_proc:
            try:
                backend_proc.terminate()
                backend_proc.wait(timeout=2)
            except Exception:
                try:
                    backend_proc.kill()
                except Exception:
                    pass

        if frontend_proc:
            try:
                if os.name == 'nt':
                    subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                else:
                    frontend_proc.terminate()
            except Exception:
                pass
        logger.info("💀 Все сервисы успешно остановлены. Порты очищены. Выход.")


if __name__ == "__main__":
    main()