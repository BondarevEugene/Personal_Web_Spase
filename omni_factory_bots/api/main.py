# api/main.py
from fastapi import FastAPI, Depends
from core.module_manager import ModuleManager
from core.compiler import BotCompiler

app = FastAPI()


@app.get("/api/registry")
def get_registry():
    """Отдает список 51 модуля для левой панели конструктора"""
    return ModuleManager.get_ui_registry()


@app.post("/api/deploy/{client_id}/{bot_id}")
def deploy_bot(client_id: int, bot_id: int, graph_data: dict):
    """Принимает JSON от Drawflow и запускает генерацию кода"""
    compiler = BotCompiler(client_id, bot_id, graph_data)
    result = compiler.build()

    # Изменение статуса в БД на 'production'
    # db.update_bot_status(bot_id, 'production')

    return {"status": "success", "message": result}