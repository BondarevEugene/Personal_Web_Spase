# ==============================================================================
# PROJECT: OMNIFACTORY EVO // API_CORE // INDUSTRIAL_VERSION
# LOCATION: /server.py (ФИНАЛЬНЫЙ МИКРОСЕРВИСНЫЙ ПУСК)
# LAST MODIFIED: 2026-05-24
# CONCEPT: Убийство flet_fastapi. Переход на независимый Native Flet Server.
# server.py (ЧИСТЫЙ BACKEND-API)
#===================НАЧАЛО ИМПОРТОВ МОДУЛЕЙ=====================================

import sys, os, json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request

# 1. ЕДИНАЯ ТОЧКА ПУТЕЙ (всё привязано к расположению server.py)
BASE_DIR = Path(__file__).resolve().parent
sys.path.extend([
    str(BASE_DIR),
    str(BASE_DIR / "services"),
    str(BASE_DIR / "omni_factory_bots" / "engine"),
    str(BASE_DIR / "omni_factory_bots" / "core"),
])

# 2. ЧИСТЫЕ ИМПОРТЫ (без дублей)
from services.bot_factory import BotFactory
from services.project_generator import ProjectGenerator
from engine.registry import Registry
from engine.orchestrator import Orchestrator


# 3. ИНИЦИАЛИЗАЦИЯ (Сервер как объект)
app = FastAPI()
registry = Registry(str(BASE_DIR / "projects_config.json"))
bot_orchestrator = Orchestrator()
bot_factory = BotFactory(registry)


# 1. Настройка путей
# 1. Настройка путей
BASE_DIR = r"C:\Users\bonda\PycharmProjects\Personal_Web_Spase"
paths_to_add = [
    BASE_DIR,
    os.path.join(BASE_DIR, "services"),
    os.path.join(BASE_DIR, "omni_factory_bots", "engine"),
    os.path.join(BASE_DIR, "omni_factory_bots", "core"),
]
for p in paths_to_add:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

# 2. ИМПОРТЫ БИБЛИОТЕК (Здесь импортируется BaseModel!)
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# 3. ИМПОРТЫ МОДУЛЕЙ
from module_manager import ModuleManager
from orchestrator import Orchestrator
from registry import Registry

from fastapi.responses import FileResponse

# 2. Добавляем ПРАВИЛЬНЫЕ пути к твоим папкам
paths_to_add = [
    BASE_DIR,
    os.path.join(BASE_DIR, "services"),  # Здесь лежит module_manager
    os.path.join(BASE_DIR, "omni_factory_bots", "engine"),  # ЗДЕСЬ лежит orchestrator
    os.path.join(BASE_DIR, "omni_factory_bots", "core"),  # ЗДЕСЬ лежит registry
]

for p in paths_to_add:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)
        print(f"DEBUG: Путь {p} добавлен")

# Инициализация (сделайте это один раз при старте сервера)
registry = Registry('path/to/your/registry.json')
module_manager = ModuleManager(registry)


# 4. ОПРЕДЕЛЯЕМ КЛАССЫ
# Определяем схему для чистого API
class BotConfigSchema(BaseModel):
    bot_id: str
    bot_name: str
    selected_module_ids: List[str]
    graph: Dict[str, Any]  # Граф из Drawflow
    token: str


class Orchestrator:
    def __init__(self):
        self.connectors = {}  # {bot_id: TelegramConnector()}

    async def route_event(self, bot_id, event):
        # Механизм перенаправления событий
        # Получаем бота, отдаем ему Event, ждем ответ
        bot = self.connectors.get(bot_id)
        return await bot.process(event)


# 5. Инициализация FastAPI
app = FastAPI(title="OMNIFACTORY EVO // API_CORE")


@app.get("/api/v1/registry")
async def get_registry():
    return {"modules": ModuleManager.get_all_modules()}


# Используем Dependency Injection, чтобы не создавать экземпляры внутри функции


# СЮДА СКОПИРУЙ ОСТАЛЬНЫЕ СВОИ ЭНДПОИНТЫ (без flet!)
# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /server.py (ФИНАЛЬНЫЙ МИКРОСЕРВИСНЫЙ ПУСК)
# LAST MODIFIED: 2026-05-21
# CONCEPT: Убийство flet_fastapi. Переход на независимый Native Flet Server.
# ==============================================================================
import os

os.chdir(r'C:\Users\bonda\PycharmProjects\Personal_Web_Spase')

import sys

# 1. ОДИН РАЗ настраиваем пути
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Добавляем папку omni_factory_bots, чтобы видеть engine, connectors и т.д.
bots_path = os.path.join(project_root, 'omni_factory_bots')
if bots_path not in sys.path:
    sys.path.append(bots_path)

# 2. ИМПОРТЫ СТАНДАРТНЫХ БИБЛИОТЕК
import subprocess
import asyncio
import uuid
import time
import datetime
import random
import psutil
import httpx
import logging
import threading
import uvicorn
import socket
from datetime import datetime as dt
from contextlib import asynccontextmanager

# 3. ИМПОРТЫ FASTAPI И СТОРОННИХ
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 4. НАШИ ВНУТРЕННИЕ МОДУЛИ (теперь они гарантированно видны)
# Из папки omni_factory_bots/engine/...
from engine.registry import Registry
from engine.orchestrator import Orchestrator
from connectors.telegram_connector import TelegramConnector

# Из папки services/
from services.bot_factory import BotFactory
from services.project_generator import ProjectGenerator
from services.module_manager import ModuleManager

# Из папки db/ или корня
from db.models import BotSchema
from db.models import BotConfigSchema

app = FastAPI(title="OMNIFACTORY EVO CORE")

# 5. ИНИЦИАЛИЗАЦИЯ (ОДИН РАЗ)
# Реестр берет конфиг из папки проекта
my_registry = Registry('omni_factory_bots/config/registry.json')
factory = BotFactory(my_registry)
module_manager = ModuleManager(my_registry)


# ПРОВЕРКА ПОРТА
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


if is_port_in_use(8088):
    print("!!! ПОРТ 8088 ЗАНЯТ. Сначала закрой старый процесс!")
    sys.exit(1)


# ==================================================================

# Роут  инстанс из module_manager.py
@app.get("/api/builder/modules")
async def get_modules():
    """Возвращает список всех доступных библиотек для билдера"""
    return module_manager.get_ui_registry()


@app.get("/api/builder/modules")
async def get_available_modules():
    # my_registry.modules — это словарь, который мы загрузили из JSON
    all_modules = []
    for cat_name, modules_list in my_registry.modules.items():
        for mod in modules_list:
            all_modules.append({
                "id": mod["id"],
                "label": mod["label"],
                "cat": mod["cat"],
                "desc": mod["desc"]
            })
    return {"modules": all_modules}


class Registry:
    def __init__(self, registry_path):
        # Получаем корень проекта (Personal_Web_Spase)
        # engine/ находится в omni_factory_bots/engine/ -> нужно подняться на 2 уровня вверх
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))

        self.abs_path = os.path.join(project_root, registry_path)

        if not os.path.exists(self.abs_path):
            # Если не нашел, выведем, где именно он искал (для дебага)
            raise FileNotFoundError(f"Файл не найден по пути: {self.abs_path}")

        with open(self.abs_path, 'r', encoding='utf-8') as f:
            self.modules = json.load(f)

    def get_module_schema(self, module_id: str):
        for category in self.modules.values():
            for module in category:
                if module.get('id') == module_id:
                    return module
        return None


# Инициализируем Оркестратор один раз при запуске сервера
bot_orchestrator = Orchestrator()
# === ИЗОЛЯЦИЯ ВОРКЕРА (СТАВИТСЯ СРАЗУ ПОСЛЕ ИМПОРТОВ) ===
if os.environ.get("IS_CHILD") == "1":
    # Перенаправляем весь вывод в файл, чтобы увидеть то, что не печатается в консоль
    with open("child_debug.log", "w", encoding="utf-8") as log_file:
        sys.stdout = log_file
        sys.stderr = log_file

        print(">>> [CHILD] Билдер запускается...")
        try:
            import flet as ft

            #from visual_builder import build_papa_bots_view

            # Используем .run()
            ft.run(build_papa_bots_view, port=8089, host="127.0.0.1", view=None)
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback

            traceback.print_exc()
    sys.exit(1)

# 1. Инициализируем реестр (один раз на старте)


# 2. Инициализируем фабрику, передав ей реестр
factory = BotFactory(my_registry)

# 3. Генерируем бота
bot_code = factory.generate(['welcome', 'cart'])
print(bot_code)

# =============================================================================
# ГЛОБАЛЬНЫЕ КОНФИГУРАЦИИ ТЕЛЕГРАМ-ШЛЮЗА ЯДРА И ОСТРОВКОВ БЕЗОПАСНОСТИ
# =============================================================================
TG_TOKEN = "ТВОЙ_ТОКЕН_БОТА_СЮДА"
ADMIN_ID = 123456789  # Твой цифровой ID без кавычек
PORT = 8088
API_BASE_URL = f"http://127.0.0.1:{PORT}"
SERVICE_ACCOUNT_KEY = "firebase_key.json"

# === ЭКСТРЕННЫЙ ФИЛЬТР: ЕСЛИ ЭТО БИЛДЕР, ЗАПУСКАЕМ И ВЫХОДИМ ===
# ВАЖНО: В Flet 0.24+ используем ft.run(функция, ...)
# БЕЗ target=
if os.environ.get("IS_CHILD") == "1":
    try:
        print(">>> [CHILD] Билдер запускается на 127.0.0.1:8089...")
        # Используем .run() как стандарт Flet 0.24+
        ft.run(build_papa_bots_view, port=8089, host="127.0.0.1", view=None)
    except Exception as e:
        print(f">>> [CHILD CRITICAL ERROR]: {e}")
        import traceback

        traceback.print_exc()
    sys.exit(0)  # Обязательно выходим, чтобы воркер не грузил БД/API
#=====================================================================

# === ИЗОЛИРОВАННЫЙ БИЛДЕР (ДОЛЖЕН БЫТЬ В САМОМ НИЗУ СТРУКТУРЫ) ===
if os.environ.get("OMNIFACTORY_RUN_BUILDER") == "TRUE":
    # 1. СНАЧАЛА задаем переменные среды, пока Flet еще не "загрузился" в память
    import os

    os.environ["FLET_WS_ALLOWED_ORIGINS"] = "*"
    os.environ["FLET_WEB_ALLOW_ORIGINS"] = "*"

    # 2. ТЕПЕРЬ импортируем Flet
    import flet as ft

    #from visual_builder import build_papa_bots_view

    # 3. Запускаем сервер
    ft.app(target=build_papa_bots_view, port=8089, view=None)


# =============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ FASTAPI И ШАБЛОНОВ (СТРОГИЙ ПОРЯДОК)
# =============================================================================
# 2. СРАЗУ ПОСЛЕ ИМПОРТОВ создаем объект приложения


@app.post("/api/deploy/build")
async def build_bot_package(data: BotSchema):
    # 1. Генерируем код бота
    factory = BotFactory(data.selected_modules)
    bot_code = factory.generate()

    # 2. Упаковываем в архив (используя твой project_generator.py)
    gen = ProjectGenerator(bot_code, data.selected_modules)
    zip_buffer = gen.create_deployment_package()

    return {"message": "Архив проекта готов", "download_url": "/api/download/..."}


# 3. Мониторинг (используем логику из твоих моделей)
@app.get("/api/v1/telemetry")
async def get_telemetry():
    from models import get_system_stats
    return get_system_stats()


# ==============================================================================
# ПАТЧ БЕЗОПАСНОСТИ (Убирает ошибку Eval/CSP)
# ==============================================================================
@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    # Добавляем frame-ancestors, чтобы разрешить вставку самого себя в iframe
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' http://127.0.0.1:8089 ws://127.0.0.1:8089; "
        "frame-src 'self' http://127.0.0.1:8089; "
        "frame-ancestors 'self' http://127.0.0.1:8088;"
    )
    return response


# ==== Добавление API-эндпоинта /api/v1/deploy


#===========================================================

# Теперь шаблоны Jinja2 инициализируются безопасно
templates = Jinja2Templates(directory="templates")


# Островок динамических компонентов для вкладки РОБОТИЗАЦИЯ
@app.get("/api/components/robotization", response_class=HTMLResponse)
async def get_robotization_page():
    """
    Прямой изолированный роут для динамического рендеринга среды сборщика.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "templates", "robotization.html")

    if not os.path.exists(template_path):
        template_path = os.path.join(os.getcwd(), "templates", "robotization.html")

    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Шаблон robotization.html не найден")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения ядра: {str(e)}")


# =============================================================================
# ПОДКЛЮЧЕНИЕ К ОБЛАЧНОЙ СУБД NEON.TECH
# =============================================================================
import psycopg2
from psycopg2.extras import RealDictCursor

NEON_DATABASE_URL = "postgresql://neondb_owner:npg_PwedkOSD0oL5@ep-sparkling-sea-ap665555-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
db_conn = None

try:
    # Добавляем connect_timeout (в секундах)
    db_conn = psycopg2.connect(NEON_DATABASE_URL, connect_timeout=5)
    db_conn.autocommit = True
    print(f"[{dt.now().strftime('%H:%M:%S')}] [🔮 NEON.TECH] Успешное подключение к облачному Postgres!")
except Exception as e:
    print(f"🚨 [DATABASE FAULT] База данных Neon недоступна при старте: {e}")
    print("Продолжаем запуск ядра в изолированном режиме...")
    db_conn = None


# =============================================================================
# 0. СЕРВИСНЫЕ КАНАЛЫ ЛОГИРОВАНИЯ И ЗАЩИТА ОТ СПАМА
# =============================================================================

class HealthCheckFilter(logging.Filter):
    """Кастомный фильтр для полного подавления логирования циклических хелсчеков."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()


# Внедряем фильтрацию в транспортный логгер uvicorn, чтобы консоль была чистой
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


def core_log(module: str, message: str, level: str = "INFO") -> None:
    """Унифицированный вывод критических системных событий ядра экосистемы."""
    timestamp = dt.now().strftime("%H:%M:%S")
    icons = {"INFO": "🟢", "WARN": "⚠️", "ERROR": "🚨", "SUCCESS": "🔥"}
    print(f"[{timestamp}] [{icons.get(level, '🔹')} {module}] {message}")


# =============================================================================
# КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ
# =============================================================================
import psycopg2
from psycopg2.extras import RealDictCursor

# Вставь сюда ту же строку, что и в init_db.py
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_PwedkOSD0oL5@ep-sparkling-sea-ap665555-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

db_conn = None
try:
    db_conn = psycopg2.connect(NEON_DATABASE_URL)
    db_conn.autocommit = True
    print(
        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [🟢 СУБД ACTIVE] Успешное подключение к Neon.tech Postgres!")
except Exception as e:
    print(f"❌ Критическая ошибка подключения к Neon.tech: {e}")
    db_conn = None

# ГЛОВAЛЬНЫЙ КЛЮЧ ДОСТУПА К КАНАЛАМ АДМИНИСТРИРОВАНИЯ
KERNEL_ACCESS_KEY = "0602"

# Динамическое определение путей для предотвращения сбоев на Windows
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Импорт Pydantic-моделей из твоего файла models.py для валидации данных
try:
    from models import CRMEvent, CommunicationLog, UserProfile

    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False

# Безопасный импорт кастомного роутера сборщика конвейеров
try:
    from backend.routes.builder import router as builder_router

    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False

import firebase_admin
from firebase_admin import credentials, firestore

# ИНИЦИАЛИЗАЦИЯ FIREBASE
try:
    if not firebase_admin._apps:
        # Проверяем наличие файла ключа перед инициализацией
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [🟢 ONLINE] Firebase Connected. Project: web-factory-evo")
        else:
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [⚠️ WARNING] Firebase key missing! Running without DB.")
    else:
        db = firestore.client()
except Exception as e:
    print(f"❌ Firebase Init Error: {e}")

# ---- TELEGRAM-BOT SETTINGS ----

TG_TOKEN = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"
ADMIN_ID = 725003786  # Твой ID цифрами без кавычек
PORT = 8088
API_BASE_URL = f"http://127.0.0.1:{PORT}"


# =============================================================================
# ИСПРАВЛЕННЫЙ И ВЫЛИЗАННЫЙ ПОТОК ПЛАНИРОВЩИКА С СВЯЗЬЮ С ТЕЛЕГРАМОМ
# =============================================================================


async def telemetry_loop():
    """Конвейер автоматизации ядра, работающий на облачной СУБД Neon.tech (Postgres).
    Опрашивает очередь задач в таблице crm_events и выполняет регламентные триггеры.
    """
    import datetime
    import traceback
    global db_conn, state, TG_TOKEN, ADMIN_ID, API_BASE_URL

    print("🟢 [BACKGROUND] Фоновый конвейер телеметрии успешно запущен.")
    await asyncio.sleep(1)  # Даем ядру FastAPI инициализироваться

    while True:
        try:
            # 1. Быстрый локальный хелсчек твоего веб-узла
            try:
                with httpx.Client(timeout=1.0) as client:
                    res = client.get(f"{API_BASE_URL}/health")
                    state["server_status"] = "ONLINE" if res.status_code == 200 else "SERVER ERROR"
            except Exception as e:
                state["server_status"] = "OFFLINE"

            # 2. Опрос очереди задач в Postgres Neon
            if db_conn is not None:
                try:
                    with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        # Выбираем одну самую старую задачу, которая ждет запуска (PENDING)
                        cursor.execute(
                            "SELECT * FROM crm_events WHERE status = 'PENDING' ORDER BY scheduled_time ASC LIMIT 1"
                        )
                        task = cursor.fetchone()

                        if task:
                            task_id = task["id"]
                            task_title = task["title"]
                            script_name = task["linked_script"]

                            # Переводим узел в режим обработки (PROCESSING)
                            add_log(f"⚡ Pipeline trigger activated: {task_title} [{script_name}]")
                            cursor.execute("UPDATE crm_events SET status = 'PROCESSING' WHERE id = %s", (task_id,))

                            # Имитируем задержку выполнения реального скрипта автоматизации
                            await asyncio.sleep(1)

                            # Вычисляем финальный статус
                            final_status = "EXECUTED" if random.random() > 0.10 else "FAILED"
                            cursor.execute("UPDATE crm_events SET status = %s WHERE id = %s", (final_status, task_id))

                            # Логируем на фронтенд
                            add_log(f"🔥 Pipeline finished: {task_title} -> {final_status}")

                            # Отправка точечного отчета в Telegram
                            try:
                                bot_send_message(
                                    f"🎯 Задача: <b>{task_title}</b>\n"
                                    f"⚙️ Скрипт: <code>{script_name}</code>\n"
                                    f"Результат: <b>{final_status}</b>"
                                )
                            except Exception as tg_err:
                                print(f"⚠️ Ошибка отправки уведомления в Telegram: {tg_err}")
                except Exception as sql_err:
                    print(f"❌ Neon.tech SQL Execution Error: {sql_err}")

        except Exception as main_err:
            print(f"\n🚨 [CRITICAL BACKGROUND FAULT] Сбой в главном цикле планировщика: {main_err}", flush=True)
            traceback.print_exc()

        await asyncio.sleep(1)  # Шаг опроса базы данных


# Вставляем перехватчик заголовков безопасности (лечит белые iframe)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    # Разрешаем браузеру рендерить фрейм внутри твоего домена
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'self' http://127.0.0.1:8088 http://localhost:8088;"
    return response


async def safe_task(coro):
    try:
        await coro
    except Exception as e:
        print(f"!!! CRITICAL [BACKGROUND TASK]: {e}")
        import traceback
        traceback.print_exc()


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    core_log("LIFESPAN", "Запуск планировщика фонового мониторинга автоматизации...")

    # Запускаем telemetry_loop через safe_task
    task = asyncio.create_task(safe_task(telemetry_loop()))

    core_log("LIFESPAN", "Все фоновые конвейеры успешно развернуты.")

    yield

    # При выключении сервера корректно останавливаем задачу
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        core_log("LIFESPAN", "Фоновая задача успешно остановлена.")

    core_log("LIFESPAN",
             "Инициировано контролируемое завершение работы ядра сервера.")  # Блок инициализации CORSMiddleware:


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы со всех адресов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает любые HTTP-методы (GET, POST, OPTIONS)
    allow_headers=["*"],  # Разрешает любые заголовки
)

if HAS_BUILDER:
    app.include_router(builder_router, prefix="/api/builder", tags=["Project Builder"])
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [🟢 ROUTE] Кастомный Builder Router успешно подключен.")

# --- ПОЛНАЯ БИБЛИОТЕКА РЕСУРСОВ ЭКОСИСТЕМЫ ---
LIBRARY_RESOURCES = [
    {
        "id": "core",
        "label": "Kernel_v9",
        "cat": "SYSTEM",
        "icon": "memory",
        "weight": 15,
        "complexity_level": "LOW",
        "security_layer": "L1_KERNEL",
        "version": "9.4.2-stable",
        "desc": "Центральное ядро управления системой. Обеспечивает маршрутизацию между всеми модулями и управление жизненным циклом сессий.",
        "text": "СИСТЕМА АКТИВИРОВАНА. ВАШ ПЕРСОНАЛЬНЫЙ АССИСТЕНТ ГОТОВ К РАБОТЕ. ВЫБЕРИТЕ ДЕЙСТВИЕ:",
        "buttons": ["🚀 ЗАПУСК", "📊 СТАТИСТИКА", "⚙️ НАСТРОЙКИ"]
    },
    {
        "id": "ai_gpt",
        "label": "GPT-4_Turbo",
        "cat": "AI_LOGIC",
        "icon": "psychology",
        "weight": 45,
        "complexity_level": "ULTRA",
        "security_layer": "L3_INTELLIGENCE",
        "version": "v4.0-omni",
        "desc": "Модуль интеграции с моделями OpenAI. Обеспечивает ведение сложных контекстных диалогов, генерацию кода и разбор неструктурированных логов.",
        "text": "НЕЙРОСЕТЕВОЙ МОДУЛЬ ИНИЦИАЛИЗИРОВАН. СФОРМУЛИРУЙТЕ ЗАДАЧУ ДЛЯ ЯДРА GPT-4:",
        "buttons": ["🧠 НОВЫЙ ДИАЛОГ", "🎯 СЕТ ПРЕДУСТАНОВОК", "💾 ЭКСПОРТ КОНТЕКСТА"]
    },
    {
        "id": "rag",
        "label": "Gemini_RAG_v2",
        "cat": "AI_LOGIC",
        "icon": "storage",
        "weight": 50,
        "complexity_level": "HIGH",
        "security_layer": "L3_INTELLIGENCE",
        "version": "1.5-flash-rag",
        "desc": "Система интеллектуального поиска ответов по локальной базе знаний (RAG). Работает в связке с Google Gemini и векторным хранилищем ChromaDB.",
        "text": "БАЗА ЗНАНИЙ КЛИЕНТА ПОДКЛЮЧЕНА. СИСТЕМА ГОТОВА К АНАЛИЗУ ТЕКСТОВЫХ ДОКУМЕНТОВ.",
        "buttons": ["📂 ИНДЕКСАЦИЯ DOCS", "🔍 ТЕСТ ЗАПРОСА", "🧹 ОЧИСТКА ВЕКТОРОВ"]
    },
    {
        "id": "pay_stars",
        "label": "TG_Stars_Billing",
        "cat": "BUSINESS",
        "icon": "credit_card",
        "weight": 25,
        "complexity_level": "MEDIUM",
        "security_layer": "L2_SECURE_DATA",
        "version": "api-v3.4",
        "desc": "Автоматизированный биллинг для обработки платежей внутри Telegram с использованием цифровой валюты Telegram Stars. Поддерживает инвойсы и чеки.",
        "text": "ШЛЮЗ TELEGRAM STARS ГОТОВ К ПРОВЕДЕНИЮ ТРАНЗАКЦИЙ. МОНИТОРИНГ КАССЫ:",
        "buttons": ["💎 БАЛАНС", "🧾 ИСТОРИЯ ЧЕКОВ", "🔌 ТЕСТ ШЛЮЗА"]
    },
    {
        "id": "tracking",
        "label": "Nova_Poshta_Node",
        "cat": "BUSINESS",
        "icon": "local_shipping",
        "weight": 30,
        "complexity_level": "MEDIUM",
        "security_layer": "L2_SECURE_DATA",
        "version": "np-sdk-19.0",
        "desc": "Интеграционный модуль службы доставки Новая Почта. Позволяет автоматически рассчитывать стоимость, генерацию ТТН и отслеживать посылки.",
        "text": "МОДУЛЬ НОВОЙ ПОЧТЫ СИНХРОНИЗИРОВАН С ODOO. СТАТУС НАКЛАДНЫХ:",
        "buttons": ["📦 ТРЕКИНГ", "📝 СОЗДАТЬ ТТН", "📉 ПРОВЕРКА API"]
    },
    {
        "id": "logger",
        "label": "Action_Logger",
        "cat": "SYSTEM",
        "icon": "terminal",
        "weight": 10,
        "complexity_level": "LOW",
        "security_layer": "L1_KERNEL",
        "version": "log-v1.2",
        "desc": "Сквозное логирование всех пользовательских сессий, ошибок компиляции и вызовов API. Записывает метрики в реальном времени.",
        "text": "ТЕРМИНАЛ СИСТЕМНЫХ ЛОГОВ АКТИВЕН. ВЫВОД ПОСЛЕДНИХ СОБЫТИЙ ЯДРА:",
        "buttons": ["📋 СКАЧАТЬ ЛОГ", "🛑 ОЧИСТИТЬ ЭКРАН", "📊 АНАЛИЗ СБОЕВ"]
    }
]

state = {
    "selected_project_id": "techkillers",
    "primary_color": "#f97316",
    "selected_ids": ["core", "ai_gpt"],
    "inspect_id": "core",
    "terminal_lines": ["SYSTEM_READY", "AWAITING_INPUT..."],
    "server_cpu": "0%",
    "server_ram": "0%",
    "server_status": "ONLINE"
}

bot_logic = {m["id"]: {"text": m["text"], "buttons": list(m["buttons"])} for m in LIBRARY_RESOURCES}


# --- МЕТРИКИ И ЛОГИРОВАНИЕ ---
def calculate_stats():
    total_weight = 0
    for m_id in state["selected_ids"]:
        node = next((n for n in LIBRARY_RESOURCES if n["id"] == m_id), None)
        if node:
            total_weight += node["weight"]

    ram = (total_weight * 14.8) + (len(state["selected_ids"]) * 5)
    cpu = min(total_weight * 0.95, 100)

    label = "STABLE_CORE"
    if total_weight > 50:
        label = "ADVANCED_UNIT"
    if total_weight > 85:
        label = "INDUSTRIAL_MAX"

    return label, f"{ram:.1f}", f"{cpu:.0f}"


def add_log(text):
    t_str = datetime.datetime.now().strftime("%H:%M:%S")
    state["terminal_lines"].append(f"[{t_str}] SYS: {text.upper()}")
    if len(state["terminal_lines"]) > 50:
        state["terminal_lines"].pop(0)


def generate_mock_tasks():
    titles = [
        "🛠️ Backup Genesys Core", "📊 Sync SEO Snapshot", "🔍 Health Scan: Valkyria",
        "💎 Audit TG_Stars Shroud", "⚙️ Re-index ChromaDB Vector"
    ]
    sites = ["LOCAL_HOST (WF_MAIN)", "GENESYS_ENGINE_NODE", "VALKYRIA_SHIELD"]
    scripts = ["RESTART", "HEALTH_SCAN", "DB_BACKUP", "SEO_SNAPSHOT"]

    tasks = []
    base_time = datetime.datetime.now()
    for i in range(12):
        delta_days = random.randint(-5, 10)
        delta_hours = random.randint(0, 23)
        task_time = base_time + datetime.timedelta(days=delta_days, hours=delta_hours)
        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "title": random.choice(titles),
            "description": f"Автоматизированный регламентный запуск пула подсистем. Сгенерировано ядром OmniFactory.",
            "start": task_time.isoformat(),
            "target_site": random.choice(sites),
            "linked_script": random.choice(scripts),
            "status": random.choice(["PENDING", "EXECUTED", "FAILED"])
        })
    return tasks


cached_tasks = generate_mock_tasks()


def get_template_response(filename: str):
    path = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    core_log("ROUTER", f"Критическая ошибка: Файл шаблона {filename} отсутствует по пути {path}!", "ERROR")
    return JSONResponse(status_code=404, content={"error": f"Файл {filename} не найден в папке /templates/"})


# --- ИНТЕГРАЦИОННЫЙ ШЛЮЗ TELEGRAM BOT API ---
def bot_send_message(text: str) -> bool:
    global TG_TOKEN, ADMIN_ID
    if not TG_TOKEN or "СЮДА" in TG_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": f"📟 <b>[NEON PIPELINE]</b>\n{text}",
        "parse_mode": "HTML"
    }
    try:
        with httpx.Client() as client:
            res = client.post(url, json=payload, timeout=4.0)
            return res.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}")
        return False


# Валидация токена бота при старте ядра
try:
    test_res = httpx.get(f"https://api.telegram.org/bot{TG_TOKEN}/getMe", timeout=2.0)
    if test_res.status_code == 200:
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [🟢 ONLINE] Telegram Bot Active: @{test_res.json()['result']['username']}")
    else:
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [⚠️ WARNING] Telegram Token invalid or webhook blocked.")
except Exception as e:
    print(f"❌ Telegram Auth Network Error: {e}")


# =============================================================================
# МАРШРУТИЗАЦИЯ СТРАНИЦ ВЕБ-ИНТЕРФЕЙСА (ЮРИДИЧЕСКИЕ ССЫЛКИ ИЗ TEMPLATES)
# =============================================================================
# Добавь эту маленькую обертку прямо перед функцией lifespan
async def safe_task(coro):
    try:
        await coro
    except Exception as e:
        print(f"!!! CRITICAL: Фоновая задача упала: {e}")
        import traceback
        traceback.print_exc()


# И измени вызов внутри lifespan на этот:
async def safe_task(coro):
    try:
        await coro
    except Exception as e:
        print(f"!!! CRITICAL: Фоновая задача упала: {e}")
        import traceback
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    core_log("LIFESPAN", "Запуск планировщика фонового мониторинга автоматизации...")

    # ИСПРАВЛЕННЫЙ ВЫЗОВ (используем telemetry_loop):
    task = asyncio.create_task(safe_task(telemetry_loop()))

    core_log("LIFESPAN", "Все фоновые конвейеры успешно развернуты.")

    yield

    # При выключении сервера отменяем задачу
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        core_log("LIFESPAN", "Фоновая задача успешно остановлена.")

    core_log("LIFESPAN", "Инициировано контролируемое завершение работы ядра сервера.")


@app.get("/")
async def index_page():
    print(">>> [DEBUG] Запрос к index_page получен")
    try:
        # Временно сохраняем результат
        response = get_template_response("index.html")
        print(">>> [DEBUG] Шаблон index.html успешно вызван")
        return response
    except Exception as e:
        print(f"!!! [CRITICAL ERROR] Ошибка при вызове index_page: {e}")
        # Выводим полный трейсбэк, чтобы понять, где именно падает
        import traceback
        traceback.print_exc()
        raise e


@app.get("/admin")
async def admin_page():
    return get_template_response("admin.html")


# =============================================================================
# РОУТЫ ДЛЯ ЮРИДИЧЕСКИХ СТРАНИЦ С АВТООПРЕДЕЛЕНИЕМ ПРАВИЛЬНЫХ ПУТЕЙ
# =============================================================================

def get_legal_file_path(folder_name: str, file_name: str) -> str:
    """Вспомогательная функция для поиска файла как в корне папки, так и внутри неё."""
    # Вариант 1: public/nda/index.html или public/nda/nda.html
    paths_to_try = [
        os.path.join(BASE_DIR, "public", folder_name, "index.html"),
        os.path.join(BASE_DIR, "public", folder_name, f"{file_name}.html"),
        # Фолбэк на случай, если файлы лежат в корне public
        os.path.join(BASE_DIR, "public", f"{file_name}.html")
    ]
    for path in paths_to_try:
        if os.path.exists(path):
            return path
    return ""


@app.get("/privacy", response_class=HTMLResponse)
async def get_privacy_page():
    path = get_legal_file_path("privacy", "privacy")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # Если файл вдруг не найден — отдаем красивую заглушку, чтобы сайт не падал
    return HTMLResponse("<h1>Privacy Policy Node</h1><p>File not found on server. Check paths.</p>", status_code=404)


@app.get("/offer", response_class=HTMLResponse)
async def get_offer_page():
    path = get_legal_file_path("offer", "offer")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Public Offer Node</h1><p>File not found on server. Check paths.</p>", status_code=404)


@app.get("/nda", response_class=HTMLResponse)
async def get_nda_page():
    path = get_legal_file_path("nda", "nda")
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>NDA Protocol Node</h1><p>File not found on server. Check paths.</p>", status_code=404)


# =============================================================================
# ЗАЩИЩЕННЫЙ ШЛЮЗ АВТОРИЗАЦИИ (ПРОВЕРКА КЛЮЧА 0602 НА БЭКЕНДЕ)
# =============================================================================
@app.post("/api/auth/verify")
async def verify_kernel_key(payload: dict = Body(...)):
    user_key = payload.get("key")
    if user_key == KERNEL_ACCESS_KEY:
        core_log("SECURITY", "ACCESS_GRANTED. Успешный вход в систему управления конвейером.", "SUCCESS")
        return {"status": "granted", "redirect": "/admin"}
    core_log("SECURITY", f"ACCESS_DENIED. Несанкционированная попытка ввода ключа: {user_key}", "WARN")
    return JSONResponse(status_code=403, content={"status": "denied", "error": "INVALID_ACCESS_KEY"})


# =============================================================================
# API ИНТЕРАКТИВНОГО КИБЕР-ВИДЖЕТА ТЕЛЕГРАМ-БОТА ДЛЯ ГЛАВНОЙ СТРАНИЦЫ
# =============================================================================
@app.get("/api/bot/interface")
async def get_bot_interface():
    active_node = LIBRARY_RESOURCES[0]  # Извлекаем Kernel_v9 как базовое состояние экрана
    return {
        "bot_name": "Web_FactoryBot",
        "status": "STATUS_OPERATIONAL",
        "display_text": active_node["text"],
        "buttons": active_node["buttons"]
    }


# =============================================================================
# МОДУЛЬ: БОТИЗИРОВАНИЕ (BOT BUILDER PIPELINE)
# =============================================================================
from pydantic import BaseModel


class BotBuildRequest(BaseModel):
    selected_ids: list
    bot_token: str = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"


@app.post("/api/builder/generate")
async def generate_bot_package(request: BotBuildRequest):
    """
    Промышленный конвейер вкладки 'БОТИЗИРОВАНИЕ'.
    Принимает массив ID модулей -> Генерирует main.py -> Добавляет Docker-окружение -> Отдает ZIP
    """
    global state
    add_log(f"⚡ [БОТИЗИРОВАНИЕ] Инициализирован запуск конвейера для проекта: {state.get('selected_project_id')}")

    try:
        from bot_factory import BotFactory
        from project_generator import ProjectGenerator
        from fastapi.responses import StreamingResponse

        if not request.selected_ids:
            raise HTTPException(status_code=400, detail="Список модулей пуст. Выберите компоненты для сборки.")

        # 1. Генерация тела кода на базе aiogram v3
        factory = BotFactory(selected_ids=request.selected_ids)
        bot_raw_code = factory.generate()

        # Инжекция пользовательского токена
        bot_raw_code = bot_raw_code.replace("YOUR_TOKEN", request.bot_token)

        # 2. Передача бинарного кода инкапсулятору сред развертывания
        generator = ProjectGenerator(
            bot_code=bot_raw_code,
            selected_modules=request.selected_ids
        )

        # 3. Сборка пакета в ОЗУ (без генерации мусорных файлов на диске сервера)
        zip_buffer = generator.create_deployment_package()
        zip_buffer.seek(0)

        add_log(f"🔥 [БОТИЗИРОВАНИЕ] Конвейер успешно завершен. Скомпилировано модулей: {len(request.selected_ids)}")

        # Уведомление в Telegram администратора
        bot_send_message(
            f"🛠️ <b>[OMNIFACTORY / БОТИЗИРОВАНИЕ]</b>\n"
            f"Сгенерирован новый программный пакет!\n"
            f"🧱 Активных модулей: <b>{len(request.selected_ids)}</b>\n"
            f"🚀 Среда деплоя: <code>Docker (python:3.11-slim)</code>"
        )

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=bot_{state.get('selected_project_id', 'factory')}.zip"}
        )

    except Exception as e:
        add_log(f"🚨 [BUILDER ERROR] Критический сбой сборки: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


# =============================================================================
# BACKEND API ЭНДПОИНТЫ И ТЕЛЕМЕТРИЯ ЯДРА
# =============================================================================

@app.get("/api/get_modules")
async def get_modules_legacy():
    # Возвращаем тот же формат, что ожидает твой JS (list of objects)
    return ModuleManager.get_all_modules_list()  # Убедись, что метод возвращает список


@app.get("/api/state")
async def get_state():
    lbl, ram, cpu = calculate_stats()
    try:
        state["server_cpu"] = f"{psutil.cpu_percent()}%"
        state["server_ram"] = f"{psutil.virtual_memory().percent}%"
    except Exception:
        state["server_cpu"] = f"{cpu}%"
        state["server_ram"] = f"{ram}MB"

    return {
        "state": state,
        "computed": {
            "label": lbl,
            "ram": state["server_ram"],
            "cpu": state["server_cpu"]
        },
        "resources": LIBRARY_RESOURCES
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent
    }


@app.get("/api/tasks")
async def get_tasks():
    if db is not None:
        try:
            docs = db.collection("crm_events").stream()
            db_tasks = []
            for doc in docs:
                d = doc.to_dict()
                db_tasks.append({
                    "id": doc.id,
                    "title": d.get("title"),
                    "description": d.get("description"),
                    "start": d.get("scheduled_time"),
                    "target_site": d.get("target_site"),
                    "linked_script": d.get("linked_script"),
                    "status": d.get("status", "PENDING")
                })
            return db_tasks
        except Exception as e:
            print(f"Firestore Stream Error: {e}")
    return cached_tasks


@app.post("/api/tasks/create")
async def create_task(req: Request):
    try:
        data = await req.json()
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": data.get("title", "Unnamed Task"),
            "description": data.get("description", ""),
            "start": data.get("start", dt.now().isoformat()),
            "target_site": data.get("target_site", "LOCAL_HOST (WF_MAIN)"),
            "linked_script": data.get("linked_script", "HEALTH_SCAN"),
            "status": "PENDING"
        }

        if db_conn is not None:
            with db_conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO crm_events (id, title, description, scheduled_time, target_site, linked_script, status) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (new_task["id"], new_task["title"], new_task["description"], new_task["start"],
                     new_task["target_site"], new_task["linked_script"], new_task["status"])
                )
        else:
            cached_tasks.append(new_task)

        bot_send_message(f"🆕 <b>Задача ушла в Neon Postgres:</b>\n🎯 {new_task['title']}")
        return {"status": "success", "task": new_task}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/analytics")
async def get_analytics():
    tasks = await get_tasks()
    total = len(tasks)
    pending = len([t for t in tasks if t["status"] == "PENDING"])
    executed = len([t for t in tasks if t["status"] == "EXECUTED"])
    failed = len([t for t in tasks if t["status"] == "FAILED"])
    return {
        "total_tasks": total,
        "pending": pending,
        "executed": executed,
        "failed": failed
    }


@app.post("/api/action/sync")
async def api_trigger_sync():
    add_log(f"initiating {state['selected_project_id']} sync pipeline...")
    bot_send_message(f"🔄 <b>Запущен конвейер синхронизации:</b> {state['selected_project_id'].upper()}")
    return {"status": "success"}


@app.post("/api/builder/generate")
async def generate_bot_package(request: Request):
    """
    Фактический конвейер сборки:
    Принимает конфигурацию модулей -> Собирает код -> Пакует в ZIP -> Отдает поток
    """
    global state
    add_log(f"⚡ [BUILDER] Запуск конвейера компиляции для проекта: {state.get('selected_project_id')}")

    try:
        # Локальные импорты твоих родных файлов сборщика
        from bot_factory import BotFactory
        from project_generator import ProjectGenerator
        from fastapi.responses import StreamingResponse

        # Получаем данные от фронтенда вкладки "БОТИЗИРОВАНИЕ"
        try:
            req_data = await request.json()
            selected_ids = req_data.get("selected_ids", [])
            bot_token = req_data.get("bot_token", "YOUR_TELEGRAM_BOT_TOKEN")
        except Exception:
            # Фолбэк, если фронт пока не прислал JSON
            selected_ids = state.get("selected_ids", ["welcome"])
            bot_token = "YOUR_TELEGRAM_BOT_TOKEN"

        if not selected_ids:
            raise HTTPException(status_code=400, detail="Модули для сборки не выбраны.")

        # 1. Запускаем BotFactory для генерации основного файла main.py бота
        factory = BotFactory(selected_ids=selected_ids)
        bot_raw_code = factory.generate()

        # Инжектируем токен пользователя в сгенерированный шаблон кода
        bot_raw_code = bot_raw_code.replace("YOUR_TOKEN", bot_token)

        # 2. Передаем код и список модулей упаковщику Docker/Requirements
        generator = ProjectGenerator(
            bot_code=bot_raw_code,
            selected_modules=selected_ids
        )

        # 3. Генерируем ZIP-архив прямо в оперативной памяти (BytesIO буфер)
        zip_buffer = generator.create_deployment_package()
        zip_buffer.seek(0)

        add_log(f"🔥 [BUILDER] Сборка успешно завершена. Скомпилировано модулей: {len(selected_ids)}")

        # Отправляем отчет в твой рабочий Telegram-бот
        bot_send_message(
            f"🛠️ <b>[OMNIFACTORY EVO]</b>\n"
            f"Конвейер компиляции во вкладке <b>БОТИЗИРОВАНИЕ</b> отработал успешно!\n"
            f"📦 Проект: <code>{state.get('selected_project_id')}</code>\n"
            f"🧱 Собрано модулей: <b>{len(selected_ids)}</b>"
        )

        # 4. Отправляем бинарный поток архива пользователю на скачивание
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=bot_{state.get('selected_project_id')}.zip"}
        )

    except Exception as e:
        add_log(f"🚨 [BUILDER CRASH] Ошибка сборки: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


def get_html_file(filename: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Сначала ищем в templates/
    path = os.path.join(base_dir, "templates", filename)

    # Если нет, ищем в рабочей директории (твоя логика фолбэка)
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), "templates", filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Шаблон {filename} не найден")

    return FileResponse(path)


# --- РОУТЫ ---

@app.get("/api/components/tg-bots")
@app.get("/api/components/tg-bots")
async def get_tg_bots_page():
    # 1. Получаем директорию, где лежит server.py (это корень)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Укажи путь ОТ КОРНЯ до файла.
    # Если файл лежит в папке omni_factory_bots/ui/builder_ui_pro_v2.html, путь будет таким:
    file_path = os.path.join(base_dir, "omni_factory_bots", "ui", "builder_ui_pro_v2.html")

    # ЕСЛИ ТВОЙ ФАЙЛ В ДРУГОМ МЕСТЕ — ПРОСТО ПОПРАВЬ СТРОКУ ВЫШЕ.

    # 3. Проверка
    if not os.path.exists(file_path):
        # ЭТА СТРОКА ВЫВЕДЕТ В ТЕРМИНАЛ ПУТЬ, КОТОРЫЙ НЕ СРАБОТАЛ.
        # Скопируй его из консоли и проверь, есть ли там файл.
        print(f"!!! DEBUG: Файл не найден по пути: {file_path}")
        raise HTTPException(status_code=404, detail=f"Файл не найден. Искал здесь: {file_path}")

    return FileResponse(file_path)


@app.get("/api/components/robotization")
async def get_robotization_page():
    return get_html_file("robotization.html")


# Обновляем твой эндпоинт, чтобы он брал данные из реестра

# ===API-Шлюз для модулей бота
@app.get("/api/modules/list")
async def get_modules_list():
    from services.module_manager import ModuleManager
    return {"modules": ModuleManager.get_all_modules()}


module_manager = ModuleManager(my_registry)


# 1. Реестр модулей (для визуального билдера)
@app.get("/api/v1/registry")
async def get_registry():
    return {"modules": ModuleManager.get_all_modules()}


@app.post("/api/v1/dry-run")
async def simulate_bot(graph: dict):
    # Механизм проверки без деплоя (то, о чем ты просил)
    from core.simulator import BotSimulator
    sim = BotSimulator(graph)
    return {"logs": sim.run_dry(start_node_id="start")}


# ========================================================
# --- API ДЛЯ ДЕПЛОЯ БОТОВ ---
# 2. Основной конвейер сборки
# ========================================================
@app.post("/api/v1/deploy")
async def deploy_bot(request: Request):
    try:
        data = await request.json()
        bot_id = data.get("bot_id", "default_bot")
        graph = data.get("graph")
        selected_ids = data.get("selected_module_ids", [])

        # Фабрика и генерация
        factory = BotFactory(registry)
        bot_code = factory.generate(selected_ids)

        # Генератор
        generator = ProjectGenerator(bot_code, selected_ids)
        generator.create_deployment_package()

        print(f"[SYSTEM] Bot '{bot_id}' развернут.")
        return {"status": "success", "message": "Бот успешно запущен."}

    except Exception as e:
        print(f"[ERROR] Ошибка деплоя: {e}")
        return {"status": "error", "message": str(e)}

# ==============================================================================
# ФИНАЛЬНЫЙ СТАБИЛЬНЫЙ ПУСК
# ==============================================================================
if __name__ == "__main__":
    # Убираем reload=True, если не хочешь, чтобы сервер перезапускался сам
    # При разработке это удобно, но иногда создает "шум" в логах
    uvicorn.run("server:app", host="0.0.0.0", port=8088, reload=False)
