# api/main.py
import time
from fastapi import FastAPI, Depends
from core.module_manager import ModuleManager
from core.compiler import BotCompiler

from sqlalchemy.orm import Session
from db.models import Client  # Ваша модель, которую мы создали ранее
from db.base import get_db  # Ваша функция получения сессии БД

from fastapi import FastAPI, HTTPException

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app = FastAPI()


@app.get("/architect")
async def get_architect(request: Request):
    # Указываем имя файла, который реально лежит в templates
    return templates.TemplateResponse("builder_pro_final.html", {"request": request})


@app.get("/api/admin/clients")
async def get_clients(db: Session = Depends(get_db)):
    # Запрос всех клиентов из БД
    clients = db.query(Client).all()
    # Конвертация в формат, понятный фронтенду
    return [
        {
            "full_name": c.full_name,
            "company": c.company,
            "phone": c.phone,
            "email": c.email,
            "bot_id": c.bot_id,
            "notes": c.notes
        } for c in clients
    ]


@app.get("/admin")
async def get_admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/api/registry")
def get_registry():
    """Отдает список 51 модуля для левой панели конструктора"""
    return ModuleManager.get_ui_registry()


@app.get("/dashboard")
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/api/deploy/{client_id}/{bot_id}")
def deploy_bot(client_id: int, bot_id: int, graph_data: dict):
    """Принимает JSON от Drawflow и запускает генерацию кода"""
    compiler = BotCompiler(client_id, bot_id, graph_data)
    result = compiler.build()

    # Изменение статуса в БД на 'production'
    # db.update_bot_status(bot_id, 'production')

    return {"status": "success", "message": result}


@app.post("/api/deploy_bot")
async def deploy_bot(data: dict):
    # Сохраняем граф бота
    bot_id = data.get("bot_id")
    with open(f"bots/{bot_id}.json", "w") as f:
        json.dump(data, f)
    return {"status": "success"}


@app.post("/api/deploy_bot")
async def deploy_bot(data: dict):
    bot_id = data.get("bot_id", "default_bot")
    nodes = data.get("nodes")

    if not nodes:
        raise HTTPException(status_code=400, detail="Пустой граф!")

    # Сохраняем логику бота в папку bots/
    os.makedirs("bots", exist_ok=True)
    with open(f"bots/{bot_id}.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=4)

    return {"status": "success", "message": f"Бот {bot_id} развернут в системе."}
