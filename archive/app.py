import json
import time
import threading
import httpx
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Инициализация ядра FastAPI сервера
app = FastAPI(title="OMNIFACTORY // PIPELINE_OS", version="5.5.0")

# URL твоего FastAPI сервера
API_BASE_URL = "http://localhost:8088"

# Динамическое определение абсолютного пути к папке проекта и шаблонам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

print(f"📂 [CORE INIT] Базовая директория скрипта: {BASE_DIR}")
print(f"📂 [CORE INIT] Целевая папка шаблонов: {TEMPLATES_DIR}")

# --- ПОЛНАЯ БИБЛИОТЕКА РЕСУРСОВ (100% ТВОЙ ОРИГИНАЛ) ---
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
        "desc": "Модуль интеграции с модулями OpenAI. Обеспечивает ведение сложных контекстных диалогов, генерацию кода и разбор неструктурированных логов.",
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

# --- ГЛОБАЛЬНОЕ СОСТОЯНИЕ ЭКОСИСТЕМЫ (STATE) ---
state = {
    "selected_project_id": "techkillers",
    "primary_color": "#f97316",
    "selected_ids": ["core", "ai_gpt"],
    "inspect_id": "core",
    "terminal_lines": ["SYSTEM_READY", "AWAITING_INPUT..."],
    "server_cpu": "0%",
    "server_ram": "0%",
    "server_status": "OFFLINE"
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def calculate_stats():
    total_weight = 0
    for m_id in state["selected_ids"]:
        node = next((n for n in LIBRARY_RESOURCES if n["id"] == m_id), None)
        if node:
            total_weight += node["weight"]
    ram = (total_weight * 14.8) + (len(state["selected_ids"]) * 5)
    cpu = min(total_weight * 0.95, 100)
    label = "STABLE_CORE"
    if total_weight > 50: label = "ADVANCED_UNIT"
    if total_weight > 85: label = "INDUSTRIAL_MAX"
    return label, f"{ram:.1f}", f"{cpu:.0f}"

def add_log(text):
    t_str = datetime.now().strftime("%H:%M:%S")
    state["terminal_lines"].append(f"[{t_str}] SYS: {text.upper()}")
    if len(state["terminal_lines"]) > 50:
        state["terminal_lines"].pop(0)

def safe_read_html(filename: str) -> str:
    """Абсолютно безопасное чтение файлов из папки templates по абсолютному пути"""
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"🚨 [ОШИБКА ПУТИ] Файл отсутствует по адресу: {filepath}")
        return f"<h1>Ошибка: Файл {filename} не найден в папке templates/!</h1><p>Искали тут: {filepath}</p>"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"🚨 [ОШИБКА ДЕКОДИРОВАНИЯ] Ошибка чтения {filepath}: {str(e)}")
        return f"<h1>Internal Server Error: Ошибка разбора {filename}</h1><p>{str(e)}</p>"

# --- МАРШРУТИЗАЦИЯ СТРАНИЦ ИЗ ПАПКИ TEMPLATES ---

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return safe_read_html("index.html")

@app.get("/admin", response_class=HTMLResponse)
async def read_admin():
    return safe_read_html("admin.html")

@app.get("/nda", response_class=HTMLResponse)
async def read_nda():
    return safe_read_html("nda.html")

@app.get("/offer", response_class=HTMLResponse)
async def read_offer():
    return safe_read_html("offer.html")

@app.get("/privacy", response_class=HTMLResponse)
async def read_privacy():
    return safe_read_html("privacy.html")

# --- BACKEND API ЭНДПОИНТЫ ДЛЯ СИНХРОНИЗАЦИИ ---

@app.get("/api/state")
async def get_state():
    lbl, ram, cpu = calculate_stats()
    return JSONResponse({
        "state": state,
        "computed": {"label": lbl, "ram": ram, "cpu": cpu},
        "resources": LIBRARY_RESOURCES
    })

@app.post("/api/action/sync")
async def api_trigger_sync():
    add_log(f"initiating {state['selected_project_id']} sync pipeline...")
    return {"status": "success"}

@app.post("/api/action/compile")
async def api_trigger_compile():
    add_log(f"compilation for {state['selected_project_id']} started.")
    return {"status": "success"}

# Монтируем статические файлы относительно абсолютного пути к проекту
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

# --- ПОТОК МОНИТОРИНГА ТЕЛЕМЕТРИИ СЕРВЕРА ---
def telemetry_loop():
    while True:
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{API_BASE_URL}/health")
                if res.status_code == 200:
                    state["server_status"] = "ONLINE"
                else:
                    state["server_status"] = "SERVER ERROR"
        except Exception:
            state["server_status"] = "OFFLINE"
        time.sleep(3.0)

threading.Thread(target=telemetry_loop, daemon=True).start()

if __name__ == "__main__":
    # reload=False для стабильной изоляции процесса перезапуска в Windows при ручном запуске
    uvicorn.run(app, host="127.0.0.1", port=8088)