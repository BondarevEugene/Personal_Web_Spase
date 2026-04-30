from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging
from contextlib import asynccontextmanager

# Настройка логирования для диагностики
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- WEBFACTORY SYSTEM: ONLINE ---")
    yield
    logger.info("--- WEBFACTORY SYSTEM: OFFLINE ---")


app = FastAPI(title="WebFactory_Backend", lifespan=lifespan)

# Разрешаем фронтенду подключаться к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше заменить на конкретный адрес
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION (ЗАПОЛНИ ЭТО) ---
BOT_TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = "ТВОЙ_ID"


class ContactForm(BaseModel):
    name: str
    contact: str
    message: str


@app.post("/send-message")
async def send_to_tg(form: ContactForm):
    text = f"🧬 WEBFACTORY: НОВАЯ ЗАЯВКА\n👤 Имя: {form.name}\n📱 Связь: {form.contact}\n📝 Сообщение: {form.message}"[
           cite: 2]
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10.0)[cite: 2]
            resp.raise_for_status()
        return {"status": "ok"}[cite: 2]
    except Exception as e:
        logger.error(f"Ошибка передачи данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка Telegram API")

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "WEBFACTORY_CORE",
        "message": "System is operational. Waiting for data packets."
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)