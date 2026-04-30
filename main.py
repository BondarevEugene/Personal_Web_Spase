from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI()

# РАЗРЕШАЕМ САЙТУ ОБРАЩАТЬСЯ К БЭКЕНДУ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # После деплоя сайта здесь лучше указать его адрес
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = "ТВОЙ_ТОКЕН"
CHAT_ID = "ТВОЙ_ID"

class ContactForm(BaseModel):
    name: str
    contact: str
    message: str

@app.post("/send-message")
async def send_to_tg(form: ContactForm):
    text = f"🚀 Заявка: {form.name}\n📱 {form.contact}\n📝 {form.message}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"chat_id": CHAT_ID, "text": text})
    return {"status": "ok"}