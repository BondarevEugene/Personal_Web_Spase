from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import logging
import os
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарик ответов WALLY
WALLY_RESPONSES = {
    "привет": "СИСТЕМА: Приветствую, Архитектор. Я — WALLY-V2. Готов к передаче данных.",
    "статус": "СИСТЕМА: Все системы WEBFACTORY функционируют в штатном режиме (V5.1-MX).",
    "кто ты": "Я — асинхронный дрон-почтальон. Моя задача: доставка твоих мыслей в ядро Бондарева."
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- WEBFACTORY SYSTEM: ONLINE ---")
    yield
    logger.info("--- WEBFACTORY SYSTEM: OFFLINE ---")

app = FastAPI(title="WebFactory_Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# Рекомендую использовать переменные окружения, но для теста можно вставить сюда
BOT_TOKEN = "8756016163:AAFkGMvzuvJNvp4PxSdQ4OEbpDEmsPL3Z_c"
CHAT_ID = "725003786"

# --- МОНТИРОВАНИЕ СТАТИКИ ---
# Это позволит серверу видеть папку assets (картинки, стили)
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

class ContactForm(BaseModel):
    name: str
    contact: str
    message: str

@app.post("/send-message")
async def send_to_tg(form: ContactForm):
    # Формирование текста сообщения
    text = f"🧬 WEBFACTORY: НОВАЯ ЗАЯВКА\n👤 Имя: {form.name}\n📱 Связь: {form.contact}\n📝 Сообщение: {form.message}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            # Отправка данных в Telegram API
            resp = await client.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10.0)
            resp.raise_for_status()
        return {"status": "success", "detail": "Message sent to core"}
    except Exception as e:
        logger.error(f"Ошибка передачи данных: {e}")
        raise HTTPException(status_code=500, detail="Telegram API Error")

# --- ГЛАВНАЯ СТРАНИЦА ---
@app.get("/")
async def root():
    # Если у тебя есть index.html в корне или папке templates, отдаем его
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    # Если файла нет, отдаем статус системы
    return {
        "status": "online",
        "system": "WEBFACTORY_CORE",
        "message": "System is operational. index.html not found."
    }

    # Словарик ответов WALLY
    WALLY_RESPONSES = {
        "привет": "СИСТЕМА: Приветствую, Архитектор. Я — WALLY-V2. Готов к передаче данных.",
        "статус": "СИСТЕМА: Все системы WEBFACTORY функционируют в штатном режиме (V5.1-MX).",
        "кто ты": "Я — асинхронный дрон-почтальон. Моя задача: доставка твоих мыслей в ядро Бондарева."
    }

    @app.post("/chat")
    async def wally_chat(data: dict):
        user_text = data.get("text", "").lower().strip()

        # Ищем заготовленный ответ или даем стандартный
        reply = WALLY_RESPONSES.get(user_text, f"WALLY: Пакет '{user_text}' принят. Что-то еще или отправляем в ядро?")

        return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)