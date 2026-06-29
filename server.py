# ==============================================================================
# PROJECT: OMNIFACTORY EVO // API_CORE
# LOCATION: /server.py
# CONCEPT: Чистая инициализация без дублей и жестких путей
# ==============================================================================
# 1. ИМПОРТЫ
# ==============================================================================
import sys
import logging
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.staticfiles import StaticFiles
# Подключаем модуль ИИ-консультанта
#from backend.modules.ai_consultant import get_ai_response, set_module_status

# ==============================================================================
# 2. ПУТИ И ОКРУЖЕНИЕ
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(1, str(BASE_DIR / "services"))
sys.path.insert(2, str(BASE_DIR / "omni_factory_bots"))

# ==============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ
# ==============================================================================
app = FastAPI(title="OMNIFACTORY EVO // API_CORE")
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
# app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")

templates = Jinja2Templates(directory="templates")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmniFactory")

# ==============================================================================
# 4. ИМПОРТ МОДУЛЕЙ
# ==============================================================================
from omni_factory_bots.engine.registry import Registry
from omni_factory_bots.engine.orchestrator import Orchestrator

registry = Registry(registry_path='omni_factory_bots/config/registry.json')


@app.get("/api/builder/modules")
async def get_modules():
    """Отдает список всех модулей для меню билдера"""
    try:
        # Ваш реестр возвращает словарь категорий, превращаем в список
        all_mods = []
        for cat, mods in registry.modules.items():
            for m in mods:
                # Добавляем категорию для фронтенда
                m['cat'] = cat
                all_mods.append(m)
        return {"modules": all_mods}
    except Exception as e:
        # Логируем ошибку, чтобы видеть её в консоли
        print(f"ERROR in get_modules: {e}")
        return {"error": str(e)}


# ==============================================================================
# --- ИНИЦИАЛИЗАЦИЯ ФРОНТЕНДА ---
# ============================ JS, CSS, картинки ================================

assets_dir = FRONTEND_DIST / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
    print(f"[SUCCESS] Папка /assets примонтирована")
else:
    print(f"[WARNING] Папка {assets_dir} не найдена! Фронтенд не будет стилизован.")


# Раздаем остальные файлы (favicon.ico, index.html)
# Используем отдельный роут для index.html
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Если это API запрос — возвращаем 404 (пусть API-роуты его обрабатывают)
    if full_path.startswith("api"):
        raise HTTPException(status_code=404)

    # Для любого другого пути (например, /architect, /builder) возвращаем index.html
    return FileResponse(FRONTEND_DIST / "index.html")


#==============================================

@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIST / "index.html"
    return FileResponse(index_file) if index_file.exists() else {"error": "Frontend not built"}


# ==============================================================================
# 5. ЛОКАЛЬНЫЕ МОДУЛИ (Импортируем только тут)
# ==============================================================================
from services.module_manager import ModuleManager
from engine.registry import Registry
from engine.orchestrator import Orchestrator
from services.bot_factory import BotFactory
from services.project_generator import ProjectGenerator

# ==============================================================================
# 6. КОНТЕЙНЕРЫ
# ==============================================================================
registry = Registry(BASE_DIR / "omni_factory_bots" / "config" / "registry.json")
module_manager = ModuleManager(registry)
bot_orchestrator = Orchestrator(registry_instance=registry)
bot_factory = BotFactory(registry)


# Монтируем ассеты (JS, CSS, картинки)
# Если папка существует, монтируем её. Если нет — сервер выдаст ошибку при старте,


# 5. ОПРЕДЕЛЕНИЕ СХЕМ
class BotConfigSchema(BaseModel):
    bot_id: str
    bot_name: str
    selected_module_ids: List[str]
    graph: Dict[str, Any]
    token: str


logger.info(">>> CORE SYSTEM INITIALIZED SUCCESSFULLY")


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


@app.get("/api/v1/registry")
async def get_modules_registry():
    """
    Отдает полный список из 51+ модулей для отрисовки сайдбара и свойств.
    """
    registry_path = BASE_DIR / "config" / "registry.json"  # Убедись, что путь правильный

    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="registry.json не найден")

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


#==========GET-эндпоинт для получения списка модулей===============
@app.get("/api/v1/registry")
async def get_registry():
    # Возвращаем список ваших 4-х доступных конфигураций/модулей
    return {
        "status": "success",
        "modules": [
            {"id": "ai_processor", "name": "Neural Engine V1", "category": "ai"},
            {"id": "ai_consultant", "name": "AI Consultant RAG", "category": "ai"},
            # остальные 2 модуля...
        ]
    }


# 2. Универсальная функция для отдачи любого HTML-файла из папки templates
@app.get("/api/ui/{filename}")
async def get_ui_component(filename: str):
    if not filename.endswith('.html'):
        filename += '.html'

    # Убедись, что здесь используется путь к папке templates
    path = BASE_DIR / "templates" / filename

    if path.exists():
        return {"html": path.read_text(encoding="utf-8")}

    raise HTTPException(status_code=404, detail=f"File {filename} not found in templates")


@app.get("/api/v1/registry")
async def get_registry():
    # Путь к твоему файлу
    path = BASE_DIR / "omni_factory_bots" / "engine" / "registry.json"
    if not path.exists():
        return JSONResponse({"error": "Registry not found"}, status_code=404)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)


# Используем Dependency Injection, чтобы не создавать экземпляры внутри функции


# СЮДА СКОПИРУЙ ОСТАЛЬНЫЕ СВОИ ЭНДПОИНТЫ (без flet!)
# ==============================================================================
# PROJECT: OMNIFACTORY EVO
# LOCATION: /server.py (ФИНАЛЬНЫЙ МИКРОСЕРВИСНЫЙ ПУСК)
# LAST MODIFIED: 2026-05-21
# CONCEPT: Убийство flet_fastapi. Переход на независимый Native Flet Server.
# ==============================================================================
import os
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

# ========================React-фронтенд====================================
# ИМПОРТ компонентов. Разрешаем React-фронтенду общаться с нашим Python-API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Адрес, где крутится React
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем GET, POST запросы
    allow_headers=["*"],
)
# ==========================================================================

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


#API-роута для Реестра
@app.get("/api/v1/ui/modules")
async def get_modules_for_ui():
    """
    Отдает структурированный список модулей для сайдбара билдера.
    Использует данные из твоего registry.json через Registry().
    """
    # Предполагая, что 'registry' — это инициализированный объект Registry()
    return {"categories": registry.modules}


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
#factory = BotFactory(my_registry)

# 3. Генерируем бота
#bot_code = factory.generate(['welcome', 'cart'])
#print(bot_code)

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

# Роут для динамической подгрузки интерфейсов
# Пример для API UI (универсальный поиск):
@app.get("/api/ui/{view_name}")
async def get_ui_view(view_name: str):
    # Прямой путь к твоему файлу
    if view_name == 'builder_ui_pro_v2':
        # Формируем путь, исходя из корня проекта Personal_Web_Spase
        path = BASE_DIR / "omni_factory_bots" / "ui" / "builder_ui_pro_v2.html"
    else:
        path = BASE_DIR / "templates" / f"{view_name}.html"

    # Отладка (убедись, что в консоли PyCharm путь верный)
    print(f"DEBUG: Пытаюсь загрузить файл: {path}")

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return {"html": f.read()}
    else:
        raise HTTPException(status_code=404, detail=f"Файл не найден: {path}")


# Если нужно оставить старый метод для прямой отдачи (не через fetch):
#   @app.get("/builder")
# async def get_builder_page():
# Просто переиспользуем логику выше или возвращаем напрямую
#    path = BASE_DIR / "omni_factory_bots" / "ui" / "builder_ui_pro_v2.html"
#    if path.exists():
#        return FileResponse(path)
#     raise HTTPException(status_code=404, detail="Builder not found")

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

# ==============================================================================
# --- ИНТЕГРАЦИЯ REACT-ФРОНТЕНДА (ROBOTIZATION PRO) ---
# ==============================================================================


# 3. Дополнительно: монтируем сам index.html (обычно он лежит в корне dist)
if FRONTEND_DIST.exists():
    @app.get("/")
    async def serve_frontend():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Фронтенд не собран. Запустите 'npm run build' в папке frontend."}


#@app.get("/{full_path:path}")
#async def serve_frontend(full_path: str):
# Если путь не начинается с /api, отдаем index.html из папки dist
#   if not full_path.startswith("api"):
#        return FileResponse("frontend/dist/index.html")
#   raise HTTPException(status_code=404)


@app.get("/robotization", response_class=HTMLResponse)
async def get_robotization_page():
    """Продвинутый конструктор (React SPA)"""
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse(
        "<h1 style='color:red;'>Ошибка: React-проект не собран. Выполните 'npm run build' в папке frontend.</h1>")


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
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Монтируем статику (стили, JS, картинки)
# Это нужно, чтобы браузер мог скачать файл index-B8AxQUDX.js
dist_assets = FRONTEND_DIST / "assets"
if dist_assets.exists():
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
else:
    print(f"ПРЕДУПРЕЖДЕНИЕ: Папка {dist_assets} не найдена. Фронтенд не будет загружен.")

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

# ---- БЛОК ИНИЦИАЦИИ СТАТИСТИКИ ----
# Убедитесь, что пути указаны верно относительно BASE_DIR (корень проекта)
DIST_DIR = BASE_DIR / "frontend" / "dist"

# 1. Монтируем папку с ассетами (JS/CSS)
app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

# 2. Роут для главной страницы и всех остальных путей (React Router)
#@app.get("/{full_path:path}")
#async def serve_frontend(full_path: str):
# Если путь начинается с api — это бэкенд, его не трогаем
#    if full_path.startswith("api"):
#        raise HTTPException(status_code=404)

# Иначе отдаем главный файл фронтенда
#    return FileResponse(DIST_DIR / "index.html")

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
    # Указываем путь к папке templates
    path_to_file = BASE_DIR / "templates" / "index.html"

    if not path_to_file.exists():
        logger.error(f"Файл index.html не найден по пути: {path_to_file}")
        raise HTTPException(status_code=404, detail="Файл index.html не найден в папке templates")

    return FileResponse(str(path_to_file))


# 2. Правильный роут для билдера (с учетом новой структуры путей)
@app.get("/builder")
async def get_builder_page():
    # Используем BASE_DIR как Path (убедись, что BASE_DIR определен через Path в начале файла)
    # Приводим к str для FileResponse, чтобы избежать конфликтов типов
    file_path = BASE_DIR / "omni_factory_bots" / "ui" / "builder_ui_pro_v2.html"

    if not file_path.exists():
        logger.error(f"Файл билдера не найден: {file_path}")
        raise HTTPException(status_code=404, detail="Builder page not found")

    return FileResponse(str(file_path))


from fastapi import Request
from fastapi.responses import HTMLResponse


# ==============================================================================
# --- РОУТЫ ДЛЯ ВЫДЕЛЕННЫХ СТРАНИЦ ПЛАТФОРМЫ (STANDALONE MODE) ---
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    """Главная страница платформы (Dashboard)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def get_admin_page(request: Request):
    """Панель администратора"""
    # Рендерим админку (в неё мы встроим dashboard)
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/architect", response_class=HTMLResponse)
async def get_builder_page():
    # Роут для конструктора по вашему точному пути
    path = Path(r"C:\Users\bonda\PycharmProjects\Personal_Web_Spase\omni_factory_bots\ui\builder_ui_pro_v2.html")
    if path.exists():
        return FileResponse(path)
    return templates.TemplateResponse("builder_ui_pro_v2.html", {"request": {}})


@app.get("/analytics", response_class=HTMLResponse)
async def get_analytics_page(request: Request):
    """Изолированная страница аналитики"""
    return templates.TemplateResponse("analytics.html", {"request": request})


#@app.get("/robotization", response_class=HTMLResponse)
#async def get_robotization_page(request: Request):
#    """Страница роботизации"""
#    return templates.TemplateResponse("robotization.html", {"request": request})

@app.get("/robotization")
async def robotization():
    # Полный путь до файла
    file_path = FRONTEND_DIST / "index.html"
    print(f"DEBUG: Пытаюсь отдать файл по пути: {file_path}")
    print(f"DEBUG: Файл существует? {file_path.exists()}")
    return FileResponse(file_path)


@app.get("/projects", response_class=HTMLResponse)
async def get_projects_page(request: Request):
    """Страница проектов"""
    return templates.TemplateResponse("projects.html", {"request": request})


@app.get("/techkillers", response_class=HTMLResponse)
async def get_techkillers_page(request: Request):
    """Страница TechKillers"""
    return templates.TemplateResponse("techkillers.html", {"request": request})


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


# =============================================================================
# РОУТ ДЛЯ TG-BOTS
# =============================================================================
# Убедись, что у тебя определен объект templates (обычно он смотрит в папку templates)


@app.get("/tg-bots")
async def tg_bots_page():
    # Указываем прямой путь к твоему файлу
    path_to_ide = BASE_DIR / "templates" / "builder_ui_pro_v2.html"

    if not path_to_ide.exists():
        raise HTTPException(status_code=404, detail="IDE файл не найден")

    return FileResponse(str(path_to_ide))


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
        path = BASE_DIR / "templates" / filename

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Шаблон {filename} не найден")

    return FileResponse(path)


# --- РОУТЫ ---

@app.get("/architect", response_class=HTMLResponse)
async def get_builder_page():
    """Полноэкранный конструктор бизнес-процессов (Architect Pro) с динамическим путем"""
    # Сборка пути относительно корня проекта с помощью Path-объекта
    path = BASE_DIR / "omni_factory_bots" / "ui" / "builder_ui_pro_v2.html"

    if path.exists():
        return FileResponse(path)

    raise HTTPException(status_code=404, detail="Файл конструктора не найден по относительному пути")


# ===API-Шлюз для модулей бота
@app.get("/api/modules/list")
async def get_modules_list():
    from services.module_manager import ModuleManager
    return {"modules": ModuleManager.get_all_modules()}


module_manager = ModuleManager(my_registry)


# 1. Реестр модулей (для визуального билдера)
@app.get("/api/v1/registry")
async def get_modules_registry():
    registry_path = BASE_DIR / "config" / "registry.json"
    if not registry_path.exists():
        # Если config лежит внутри omni_factory_bots
        registry_path = BASE_DIR / "omni_factory_bots" / "config" / "registry.json"

    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="registry.json не найден")

    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/v1/registry")
async def get_registry():
    # Путь к твоему файлу
    path = BASE_DIR / "omni_factory_bots" / "engine" / "registry.json"
    if not path.exists():
        return JSONResponse({"error": "Registry not found"}, status_code=404)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)


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


@app.post("/api/plan-project")
async def plan_project(request: dict):
    # Это заглушка, которая заставит 404 превратиться в 200 OK
    return {
        "nodes": [
            {"id": "1", "label": "Бот активирован"},
            {"id": "2", "label": "RAG Модуль"}
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ]
    }


# ==============================================================================
# ЭНДПОИНТЫ ДЛЯ ИИ-КОНСУЛЬТАНТА
# ==============================================================================

class QueryModel(BaseModel):
    user_query: str


#@app.post("/api/ai-consultant/ask")
#async def ask_ai_consultant(data: QueryModel):
    """
    Маршрут для отправки вопросов ИИ-консультанту с ChromaDB
    """
    # Путь к вашей векторной базе данных Chroma
#    vector_db_path = str(BASE_DIR / "backend" / "chroma_db")

    # Вызываем функцию из ai_consultant.py
#    result = get_ai_response(data.user_query, vector_db_path)

#    if result.get("status") == "restricted":
#        raise HTTPException(status_code=503, detail=result.get("response"))

#    if result.get("status") == "error":
#        raise HTTPException(status_code=500, detail=result.get("response"))

#    return result


#@app.post("/api/ai-consultant/toggle")
#async def toggle_ai_status(active: bool):
    """
    Эндпоинт для админки (переключение флага IS_ACTIVE в ai_consultant.py)
    """
#    set_module_status(active)
#    return {"status": "success", "is_active": active}


@app.on_event("startup")
async def startup_event():
    port = 8000  # Твой порт
    print(f"\n{'=' * 50}")
    print(f"🚀 СЕРВЕР ЗАПУЩЕН И ГОТОВ К РАБОТЕ")
    print(f"🌐 Адрес API: http://127.0.0.1:{port}")
    print(f"🖥  Интерфейс: http://localhost:{port}/index.html")
    print(f"{'=' * 50}\n")


# ==============================================================================
# ФИНАЛЬНЫЙ СТАБИЛЬНЫЙ ПУСК
# ==============================================================================
if __name__ == "__main__":
    # Убираем reload=True, если не хочешь, чтобы сервер перезапускался сам
    # При разработке это удобно, но иногда создает "шум" в логах
    uvicorn.run("server:app", host="0.0.0.0", port=8088, reload=False)
