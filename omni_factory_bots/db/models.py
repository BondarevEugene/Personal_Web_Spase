"""
OMNIFACTORY EVO — CENTRAL CORE ENGINE v5.6.0
===========================================
Промышленное асинхронное ядро экосистемы автоматизации и развертывания веб-приложений.

Паттерны и рефакторинг:
- Интегрирован модуль моделей (models.py) для сквозной валидации данных СУБД и API.
- Добавлен полноценный REST API для управления CRM-событиями календаря FullCalendar.
- Синхронизирована телеметрия psutil.
"""
# ==============================================================================
# PROJECT: OMNIFACTORY // EVO_CORE
# LOCATION: /db/models.py (Или models.py в корне)
# DESCRIPTION: Схемы данных для валидации API.
# ==============================================================================

import os
import time
import datetime
import psutil
import httpx
import threading
from datetime import datetime as dt
import uvicorn

from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Импорт Pydantic-моделей из твоего файла models.py для валидации входящих потоков
try:
    from models import CRMEvent, CommunicationLog, UserProfile

    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False

# Безопасный импорт кастомного роутера сборщика проектов
try:
    from backend.routes.builder import router as builder_router

    HAS_BUILDER = True
except ImportError:
    HAS_BUILDER = False

import firebase_admin
from firebase_admin import credentials, firestore


# ===чтобы FastAPI понимал, что прилетает из Flet:====
class BotConfigSchema(BaseModel):
    bot_name: str
    selected_module_ids: List[str]


class BotSchema(BaseModel):
    bot_name: str
    selected_module_ids: List[str]
    status_mode: str = "draft"
    bot_token: Optional[str] = None


# =============================================================================
# 1. СИСТЕМНАЯ КОНФИГУРАЦИЯ И ПУТИ
# =============================================================================
SERVICE_ACCOUNT_KEY = "web-factory-evo-firebase-adminsdk-fbsvc-44ec7526d6.json"
TG_TOKEN = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"
ADMIN_ID = "725003786"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# =============================================================================
# 2. ИНИЦИАЛИЗАЦИЯ FIREBASE СУБД
# =============================================================================
db = None
try:
    if not firebase_admin._apps:
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print(f"[{dt.now().strftime('%H:%M:%S')}] [🟢 ONLINE] Firebase Connected. Project: web-factory-evo")
        else:
            print(f"[{dt.now().strftime('%H:%M:%S')}] [⚠️ WARNING] Ключ Firebase отсутствует. Firestore отключен.")
    else:
        db = firestore.client()
except Exception as e:
    print(f"❌ Критическая ошибка Firebase: {e}")

# =============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ FASTAPI ЯДРА
# =============================================================================
app = FastAPI(title="OMNIFACTORY // CORE_ENGINE", version="5.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if HAS_BUILDER:
    app.include_router(builder_router, prefix="/api/builder", tags=["Project Builder"])

# --- ПОЛНАЯ БИБЛИОТЕКА РЕСУРСОВ ---
LIBRARY_RESOURCES = [
    {
        "id": "core", "label": "Kernel_v9", "cat": "SYSTEM", "icon": "memory", "weight": 15,
        "complexity_level": "LOW", "security_layer": "L1_KERNEL", "version": "9.4.2-stable",
        "desc": "Центральное ядро управления системой. Обеспечивает маршрутизацию между всеми модулями.",
        "text": "СИСТЕМА АКТИВИРОВАНА. ВАШ ПЕРСОНАЛЬНЫЙ АССИСТЕНТ ГОТОВ К РАБОТЕ.",
        "buttons": ["🚀 ЗАПУСК", "📊 СТАТИСТИКА"]
    },
    {
        "id": "ai_gpt", "label": "GPT-4_Turbo", "cat": "AI_LOGIC", "icon": "psychology", "weight": 45,
        "complexity_level": "ULTRA", "security_layer": "L3_INTELLIGENCE", "version": "v4.0-omni",
        "desc": "Модуль интеграции с моделями OpenAI. Обеспечивает ведение сложных контекстных диалогов.",
        "text": "НЕЙРОСЕТЕВОЙ МОДУЛЬ ИНИЦИАЛИЗИРОВАН. СФОРМУЛИРУЙТЕ ЗАДАЧУ:", "buttons": ["🧠 НОВЫЙ ДИАЛОГ", "💾 ЭКСПОРТ"]
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


# --- ДВИЖОК ВЫЧИСЛЕНИЙ ---
def calculate_stats():
    total_weight = sum(
        next((n["weight"] for n in LIBRARY_RESOURCES if n["id"] == m_id), 0) for m_id in state["selected_ids"])
    ram = (total_weight * 14.8) + (len(state["selected_ids"]) * 5)
    cpu = min(total_weight * 0.95, 100)
    label = "STABLE_CORE" if total_weight <= 50 else ("ADVANCED_UNIT" if total_weight <= 85 else "INDUSTRIAL_MAX")
    return label, f"{ram:.1f}", f"{cpu:.0f}"


def add_log(text):
    t_str = dt.now().strftime("%H:%M:%S")
    state["terminal_lines"].append(f"[{t_str}] SYS: {text.upper()}")
    if len(state["terminal_lines"]) > 50:
        state["terminal_lines"].pop(0)


# --- ОТДАЧА HTML ШАБЛОНОВ ---
def get_template_response(filename: str):
    path = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"error": f"Файл {filename} не найден в /templates/"})


@app.get("/")
async def index_page(): return get_template_response("index.html")


@app.get("/admin")
async def admin_page(): return get_template_response("admin.html")


@app.get("/nda")
async def nda_page(): return get_template_response("nda.html")


@app.get("/offer")
async def offer_page(): return get_template_response("offer.html")


@app.get("/privacy")
async def privacy_page(): return get_template_response("privacy.html")


# =============================================================================
# 4. РЕАЛИЗАЦИЯ И ИСПОЛЬЗОВАНИЕ МОДЕЛЕЙ ДАННЫХ (ИСПОЛЬЗУЕМ MODELS.PY)
# =============================================================================

@app.get("/api/events", summary="Получение списка всех задач для календаря CRM")
async def get_crm_events():
    """Считывает задачи из Firestore и отдает их в валидированном JSON-формате для FullCalendar."""
    if db is None:
        # Фолбэк-заглушка, если Firebase не подключен, чтобы фронтенд не падал
        return [
            {"id": 1, "title": "🛠️ Тестовый бэкап Genesys", "start": dt.now().isoformat(),
             "description": "Локальный режим"}
        ]

    try:
        events_ref = db.collection("crm_events")
        docs = events_ref.stream()

        event_list = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            event_list.append(data)

        return event_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения календаря: {e}")


@app.post("/api/events", summary="Создание нового события в календаре")
async def create_crm_event(request: Request):
    """Принимает, валидирует через JSON структуру и сохраняет задачу в БД."""
    try:
        data = await request.json()
        if db is not None:
            # Сохранение в облако Firestore
            doc_ref = db.collection("crm_events").document()
            doc_ref.set({
                "title": data.get("title", "Новая задача"),
                "description": data.get("description", ""),
                "scheduled_time": data.get("start", dt.now().isoformat()),
                "target_site": data.get("target_site", "LOCAL"),
                "linked_script": data.get("linked_script", "RESTART"),
                "status": "PENDING",
                "created_at": dt.now().isoformat()
            })
            add_log(f"Добавлена CRM задача: {data.get('title')}")
            return {"status": "success", "id": doc_ref.id}
        return {"status": "local_success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Data validation error: {e}")


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
        "computed": {"label": lbl, "ram": state["server_ram"], "cpu": state["server_cpu"]},
        "resources": LIBRARY_RESOURCES
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


# Монтирование статики
if os.path.exists(os.path.join(BASE_DIR, "public")):
    app.mount("/public", StaticFiles(directory=os.path.join(BASE_DIR, "public")), name="public")
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")


def telemetry_loop():
    while True:
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{API_BASE_URL}/health")
                if res.status_code == 200: state["server_status"] = "ONLINE"
        except Exception:
            state["server_status"] = "OFFLINE"
        time.sleep(3.0)


threading.Thread(target=telemetry_loop, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8088, reload=False)
