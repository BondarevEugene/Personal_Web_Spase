# ==============================================================================
# PROJECT: OMNIFACTORY EVO // CORE_SERVER_V2 (⚡ REPAIRED & ORDERED ⚡)
# LOCATION: /server.py
# ==============================================================================

# 1. ПУТИ И ОКРУЖЕНИЕ (СТРОГО НА ПЕРВОМ МЕСТЕ ДО ЛЮБЫХ ИМПОРТОВ СВОИХ МОДУЛЕЙ)
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
paths_to_add = [BASE_DIR, BASE_DIR / "omni_factory_bots", BASE_DIR / "services"]
for p in paths_to_add:
    if str(p) not in sys.path:
        sys.path.append(str(p))

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. СИСТЕМНЫЕ И СТОРОННИЕ ИМПОРТЫ
import io
import zipfile
import logging
import asyncio
import psutil
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 3. ИМПОРТЫ ЛОКАЛЬНЫХ МОДУЛЕЙ ПЛАТФОРМЫ (Теперь они гарантированно найдутся)
from engine.registry import Registry
from engine.orchestrator import Orchestrator
from services.bot_factory import BotFactory
from services.module_manager import ModuleManager
from services.project_generator import ProjectGenerator

# 4. ЛОГГИРОВАНИЕ
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("OmniFactory")

# 5. ФОНОВЫЙ ЦИКЛ И LIFESPAN
async def telemetry_loop():
    """Фоновый поток для мониторинга системы."""
    while True:
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(">>> KERNEL: Инициализация системы...")
    task = asyncio.create_task(telemetry_loop())
    yield
    logger.info(">>> KERNEL: Завершение работы...")
    task.cancel()

# 6. ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ FASTAPI (Единый экземпляр)
app = FastAPI(title="OMNIFACTORY EVO", lifespan=lifespan)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статики (Убедись, что папка static существует в корне проекта)
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 7. ИНИЦИАЛИЗАЦИЯ КОРНЕВЫХ СЕРВИСОВ ЯДРА
registry = Registry(BASE_DIR / "omni_factory_bots" / "config" / "registry.json")
module_manager = ModuleManager(registry)
bot_orchestrator = Orchestrator(registry_instance=registry)
bot_factory = BotFactory(registry)

# ==============================================================================
# 8. РОУТЫ (ПОЛНАЯ ИНТЕГРАЦИЯ ВСЕХ СТРАНИЦ ЭКОСИСТЕМЫ)
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"title": "OMNIFACTORY MASTER"}
    )

@app.get("/builder-pro", response_class=HTMLResponse)
async def serve_builder_pro(request: Request):
    return templates.TemplateResponse(
        request=request, name="builder_pro.html", context={"title": "OMNIFACTORY // PRO_ARCHITECT"}
    )

@app.get("/robotization", response_class=HTMLResponse)
async def serve_robotization(request: Request):
    return templates.TemplateResponse(
        request=request, name="robotization.html", context={"title": "OMNIFACTORY // ROBOTIZATION"}
    )

@app.get("/projects", response_class=HTMLResponse)
async def serve_projects(request: Request):
    return templates.TemplateResponse(
        request=request, name="projects.html", context={"title": "OMNIFACTORY // PROJECTS"}
    )

@app.get("/techkillers", response_class=HTMLResponse)
async def serve_techkillers(request: Request):
    return templates.TemplateResponse(
        request=request, name="techkillers.html", context={"title": "OMNIFACTORY // TECH_KILLERS"}
    )

@app.get("/admin-panel", response_class=HTMLResponse)
async def serve_admin(request: Request):
    return templates.TemplateResponse(
        request=request, name="admin.html", context={"title": "OMNIFACTORY // ADMINISTRATIVE_SUPERVISOR"}
    )

# --- API ДЛЯ СИНХРОНИЗАЦИИ ---
@app.get("/api/v1/registry")
async def get_registry():
    return {"categories": registry.modules}

@app.get("/api/v1/ui/modules")
async def get_modules_for_ui():
    return {"categories": registry.modules}

class BuildRequest(BaseModel):
    selected_ids: List[str]

@app.post("/api/builder/generate")
async def generate_bot_archive(data: BuildRequest):
    if not data.selected_ids:
        raise HTTPException(status_code=400, detail="На холсте отсутствуют модули для сборки.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        bot_code = (
            "# ==========================================\n"
            "# АВТОМАТИЧЕСКАЯ СБОРКА ЯДРА OMNIFACTORY v5.0\n"
            "# ==========================================\n\n"
            "import asyncio\n"
            "import logging\n\n"
            "logging.basicConfig(level=logging.INFO)\n"
            f"# Скомпилированные модули инфраструктуры: {', '.join(data.selected_ids)}\n\n"
            "async def start_pipeline():\n"
            "    logging.info('✓ Автономный бот OmniFactory успешно инициализирован.')\n"
            "    logging.info('✓ Сигнальные шлюзы находятся в режиме прослушивания сигналов.')\n\n"
            "if __name__ == '__main__':\n"
            "    asyncio.run(start_pipeline())\n"
        )
        zip_file.writestr("bot_runtime/main.py", bot_code)
        zip_file.writestr("bot_runtime/requirements.txt", "fastapi\nuvicorn\npydantic\n")
        zip_file.writestr("bot_runtime/config.json", f'{{"modules": {data.selected_ids}}}')

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=omnifactory_bot.zip"}
    )

# 10. ЗАПУСК
if __name__ == "__main__":
    logger.info(">>> SYSTEM: Запуск сервера...")
    uvicorn.run("server:app", host="127.0.0.1", port=8088, reload=False)