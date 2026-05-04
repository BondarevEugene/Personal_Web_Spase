import os
import asyncio
import uuid
import time
import datetime
import random
import psutil
import httpx
import uvicorn  # Импорт добавлен

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import firebase_admin
from firebase_admin import credentials, firestore

# ==============================================================================
# КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ
# ==============================================================================
SERVICE_ACCOUNT_KEY = "web-factory-evo-firebase-adminsdk-fbsvc-44ec7526d6.json"
TG_TOKEN = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"
ADMIN_ID = "725003786"

# ИНИЦИАЛИЗАЦИЯ FIREBASE
try:
    if not firebase_admin._apps:
        # Проверяем наличие файла ключа перед инициализацией
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [🟢 ONLINE] Firebase Connected. Project: {firebase_admin.get_app().project_id}")
        else:
            print(f"[⚠️ WARNING] Firebase key file not found. Database will be disabled.")
    db = firestore.client() if firebase_admin._apps else None
except Exception as e:
    print(f"[🔴 ERROR] Firebase Critical Failure: {e}")
    db = None

app = FastAPI(title="Web Factory Evo Core Full")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ПУТИ К ФАЙЛАМ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
ASSETS_PATH = os.path.join(BASE_DIR, "assets")

# Создаем папки, если их нет, чтобы избежать ошибок StaticFiles
if not os.path.exists(TEMPLATES_DIR): os.makedirs(TEMPLATES_DIR)
if not os.path.exists(ASSETS_PATH): os.makedirs(ASSETS_PATH)

app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")

# Глобальное состояние системы
SYSTEM_STATE = {
    "panic_mode": False,
    "last_health_status": "OK",
    "start_time": time.time()
}


# ==============================================================================
# МОДУЛЬ СБОРКИ (WEBFACTORY BUILDER)
# ==============================================================================

@app.post("/api/builder/generate")
async def generate_project(request: Request):
    try:
        data = await request.json()
        # Принимаем 'user' от фронтенда (BotBuilder.tsx)
        author = data.get('user', 'Bondarev_E')
        modules = data.get('modules', [])

        print(f"\n{'=' * 60}\n[🚀 WEBFACTORY BUILDER] Запуск потока сборки")
        print(f"[👤 OPERATOR]: {author}")
        print(f"[📦 MODULES]: {', '.join(modules)}")

        if not modules:
            print("[⚠️ ABORT] Список модулей пуст")
            return JSONResponse(status_code=400, content={"status": "ERROR", "msg": "No modules selected"})

        # Имитация процесса компиляции
        await asyncio.sleep(1.5)

        build_id = f"WF-EVO-{str(uuid.uuid4())[:8].upper()}"

        build_entry = {
            "build_id": build_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "author": author,
            "modules": modules,
            "status": "COMPLETED",
            "telemetry": {
                "cpu": f"{psutil.cpu_percent()}%",
                "ram": f"{psutil.virtual_memory().percent}%"
            }
        }

        if db:
            db.collection("build_history").document(build_id).set(build_entry)
            print(f"[✅ FIRESTORE] Сборка {build_id} сохранена в облако.")
        else:
            print("[🟠 BYPASS] Firebase не активен, запись пропущена.")

        print(f"[🏁 SUCCESS] Проект {build_id} готов к деплою.\n{'=' * 60}")

        return {
            "status": "COMPLETED",
            "build_id": build_id,
            "author": author,
            "message": f"Проект {build_id} успешно сгенерирован.",
            "artifacts": {"main_file": "bot_core.py", "config": "env.json"}
        }
    except Exception as e:
        print(f"[❌ CRITICAL ERROR] Ошибка сборщика: {e}")
        return JSONResponse(status_code=500, content={"status": "ERROR", "msg": str(e)})


# ==============================================================================
# МОДУЛЬ АНАЛИТИКИ (SITE ANALYZER)
# ==============================================================================

@app.post("/analyze-site")
async def analyze_site(request: Request):
    try:
        data = await request.json()
        url = data.get("url", "")
        if not url.startswith("http"):
            url = "https://" + url

        print(f"[🔍 ANALYZER] Анализ URL: {url}")
        start_time = time.time()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            html = response.text.lower()

            techs = []
            if "react" in html: techs.append("React.js")
            if "vue" in html: techs.append("Vue.js")
            if "wordpress" in html: techs.append("WordPress")
            if "next.js" in html: techs.append("Next.js")

            scripts_count = html.count("<script")
            estimated_price = 1500 + (scripts_count * 15)

            result = {
                "architecture": " + ".join(techs) if techs else "Custom Architecture",
                "price": f"${int(estimated_price)}",
                "metrics": {"latency": f"{int((time.time() - start_time) * 1000)}ms"},
                "scripts_found": scripts_count
            }
            print(f"[✅ ANALYZER] Результат: {result['architecture']}, Price: {result['price']}")
            return result
    except Exception as e:
        print(f"[❌ ANALYZER ERROR] {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})


# ==============================================================================
# МОДУЛЬ НАДЗОРА И СИСТЕМНЫЕ РОУТЫ
# ==============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "OPERATIONAL",
        "panic": SYSTEM_STATE["panic_mode"],
        "uptime": f"{int(time.time() - SYSTEM_STATE['start_time'])}s",
        "telemetry": {
            "cpu_load": f"{psutil.cpu_percent()}%",
            "ram_usage": f"{psutil.virtual_memory().percent}%"
        }
    }


@app.post("/panic")
async def toggle_panic():
    SYSTEM_STATE["panic_mode"] = not SYSTEM_STATE["panic_mode"]
    status_text = "⚠️ ACTIVATED" if SYSTEM_STATE["panic_mode"] else "✅ DEACTIVATED"
    print(f"[🚨 SYSTEM] PANIC MODE {status_text}")
    return {"panic_mode": SYSTEM_STATE["panic_mode"], "message": status_text}


@app.post("/chat")
async def chat_to_telegram(request: Request):
    try:
        data = await request.json()
        msg = data.get("text", "")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": ADMIN_ID, "text": f"🚀 WEB_MESSAGE: {msg}"}
            )
        return {"status": "sent", "reply": "Sent to Telegram"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


@app.get("/")
async def index():
    if SYSTEM_STATE["panic_mode"]:
        return JSONResponse({"status": "LOCKED", "message": "Maintenance Mode"})
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found", "hint": "Создайте папку 'templates' и положите туда index.html"}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏭 WEBFACTORY EVO CORE ENGINE STARTED ON PORT 8088")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8088)