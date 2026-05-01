import httpx
import random
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Монтируем папку с ресурсами, чтобы файлы были доступны по сети
# Важно: указывай путь к корневой папке assets
app.mount("/assets", StaticFiles(directory=r"C:\Users\bonda\PycharmProjects\Personal_Web_Spase\assets"), name="assets")

# Используем относительный путь (от корня проекта)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Монтируем статику
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/get-project-images/{project_name}")
async def get_images(project_name: str):
    # Путь теперь строится относительно папки проекта
    target_dir = os.path.join(ASSETS_DIR, "projects", project_name, "img")

    if not os.path.exists(target_dir):
        return []

    # Собираем список файлов
    images = [
        f"/assets/projects/{project_name}/img/{f}"
        for f in os.listdir(target_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ]
    return images


# Состояние системы
SYSTEM_STATE = {
    "panic_mode": False,
    "last_health_status": "OK"
}

TG_TOKEN = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"
ADMIN_ID = "725003786"


@app.get("/")
async def index():
    if SYSTEM_STATE["panic_mode"]:
        # Здесь должна быть страница maintenance.html
        return JSONResponse({"status": "MAINTENANCE_MODE", "msg": "System upgrading..."})
    return FileResponse("index.html")


@app.get("/health")
async def health_check():
    # Симуляция случайной ошибки API (1 из 10 запросов)
    if random.random() < 0.1:
        SYSTEM_STATE["last_health_status"] = "ERROR"
        return JSONResponse(status_code=500, content={"status": "CRITICAL_ERROR"})

    SYSTEM_STATE["last_health_status"] = "OK"
    return {"status": "OPERATIONAL", "panic": SYSTEM_STATE["panic_mode"]}


@app.post("/panic")
async def toggle_panic():
    SYSTEM_STATE["panic_mode"] = not SYSTEM_STATE["panic_mode"]
    return {"new_state": SYSTEM_STATE["panic_mode"]}


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("text", "")
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": f"🚀 WALLY_CHAT: {msg}"}
        )
    return {"reply": f"Ввод '{msg}' принят. Данные переданы Архитектору."}


@app.get("/system-override")
async def admin():
    return FileResponse("admin.html")
