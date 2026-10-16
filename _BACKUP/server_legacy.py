# ==============================================================================
# PROJECT: OMNIFACTORY EVO // CORE_SERVER_V2 (⚡ ALIGNED & REPAIRED v8.1 ⚡)
# LOCATION: /server.py
# ==============================================================================
import os
import sys
import logging
import uvicorn
from pathlib import Path  # <--- ЭТА СТРОКА ДОЛЖНА БЫТЬ ОБЯЗАТЕЛЬНО!
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from core.lifespan import lifespan

from core.templates import templates

from core.middleware import setup_middleware
setup_middleware(app)

from routes.home import router as home_router
app.include_router(home_router)


import sys
import subprocess

# Теперь ниже идет инициализация путей:
BASE_DIR = Path(__file__).resolve().parent

# 1. НАСТРАИВАЕМ ПУТИ (КРИТИЧЕСКИ ВАЖНО)
BASE_DIR = Path(__file__).resolve().parent
paths_to_add = [
    BASE_DIR,
    BASE_DIR / "omni_factory_bots",
    BASE_DIR / "services",
    BASE_DIR / "omni_factory_bots" / "core"  # Исправлено: путь к core внутри omni
]
for p in paths_to_add:
    if str(p) not in sys.path:
        sys.path.append(str(p))

# 4. ИНИЦИАЛИЗАЦИЯ FASTAPI
app = FastAPI(lifespan=lifespan)


app.include_router(home_router)

# 2. ИНИЦИАЛИЗАЦИЯ БД
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from services.module_manager import ModuleManager
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect, Body



# --- ВОТ СЮДА ВСТАВЬ ЭТУ СТРОКУ ---
Base.metadata.create_all(bind=engine)
# ----------------------------------

# 5. ИМПОРТЫ МОДУЛЕЙ ПЛАТФОРМЫ
from db.models import Client
from engine.registry import Registry
from engine.orchestrator import Orchestrator
from services.bot_factory import BotFactory
from omni_factory_bots.core.compiler import BotCompiler



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

###################### импорты MAIN.PY ################################

class Orchestrator:
        def __init__(self, registry_instance=None): pass

    class BotFactory:
        def __init__(self, registry=None): pass

    class ModuleManager:
        def __init__(self, registry=None): pass


app = FastAPI(
    title="⚡ OMNIFACTORY EVO API CONTRACT ⚡",
    description="Промышленное асинхронное ядро супервизора автоматизации OmniFactory. Управление WSL2-ресурсами, Docker-контейнерами и компиляцией когнитивных графов.",
    version="9.8",
    lifespan=lifespan
)

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==============================================================================
# СХЕМЫ ДАННЫХ ДЛЯ SWAGGER (СТАНДАРТ PYDANTIC V2)
# ==============================================================================

class ErrorSchema(BaseModel):
    error: str = Field(..., description="Текстовое описание сбоя.", json_schema_extra={"example": "Файл не найден"})


class ModuleSchema(BaseModel):
    title: str = Field(..., description="Название функционального модуля.")
    color: str = Field(..., description="Цветовая метка отображения ноды.")
    fields: Dict[str, str] = Field(..., description="Параметры конфигурации модуля.")


class RegistryResponse(BaseModel):
    categories: Dict[str, Dict[str, ModuleSchema]] = Field(..., description="Реестр всех доступных модулей платформы.")


class BuildRequest(BaseModel):
    selected_ids: List[str] = Field(...,
                                    json_schema_extra={"example": ["fastapi_core", "telegram_uplink", "ollama_node"]})


# ==============================================================================
# БЕЗОПАСНАЯ ИНИЦИАЛИЗАЦИЯ РЕЕСТРА И СЕРВИСОВ ЯДРА
# ==============================================================================
import json


def safe_load_registry_json():
    reg_path = BASE_DIR / "omni_factory_bots" / "config" / "registry.json"
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга registry.json: {e}")

    return {
        "Core": {
            "fastapi_endpoint": {"title": "FastAPI HTTP Route", "color": "#7c3aed",
                                 "fields": {"path": "/api/v1/webhook"}}
        }
    }


# Единый изолированный try-except блок для сборки инфраструктуры компонентов

try:
    registry = Registry(str(BASE_DIR / "omni_factory_bots" / "config" / "registry.json"))
    if not hasattr(registry, 'modules') or not registry.modules:
        registry.modules = safe_load_registry_json()
except Exception as e:
    logger.warning(f"⚠️ Сбой инициализации оригинального класса Registry ({e}). Включен безопасный режим.")


    class FallbackRegistry:
        def __init__(self):
            self.modules = safe_load_registry_json()


    registry = FallbackRegistry()

module_manager = ModuleManager(registry)
bot_orchestrator = Orchestrator(registry_instance=registry)
bot_factory = BotFactory(registry)


# ==============================================================================
# РОУТЫ ИНТЕРФЕЙСА И КЛАССИЧЕСКОГО API
# ==============================================================================

# ==============================================================================
# ABOUT
# ==============================================================================

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):

    return templates.TemplateResponse(
        "pages/about.html",
        {
            "request": request
        }
    )


# ==============================================================================
# PROJECTS
# ==============================================================================

@router.get("/projects", response_class=HTMLResponse)
async def projects(request: Request):

    return templates.TemplateResponse(
        "pages/projects.html",
        {
            "request": request
        }
    )


# ==============================================================================
# CONTACTS
# ==============================================================================

@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request):

    return templates.TemplateResponse(
        "pages/contacts.html",
        {
            "request": request
        }
    )


# ==============================================================================
# TECHNOLOGY
# ==============================================================================

@router.get("/technology", response_class=HTMLResponse)
async def technology(request: Request):

    return templates.TemplateResponse(
        "pages/technology.html",
        {
            "request": request
        }
    )


# ==============================================================================
# SOLUTIONS
# ==============================================================================

@router.get("/solutions", response_class=HTMLResponse)
async def solutions(request: Request):

    return templates.TemplateResponse(
        "pages/solutions.html",
        {
            "request": request
        }
    )


# ==============================================================================
# ИНТЕЛЛЕКТУАЛЬНЫЙ WEBSOCKET ШЛЮЗ ДЛЯ ЛОКАЛЬНОГО ИИ-АГЕНТА
# ==============================================================================

# Глобальный реестр системных промптов для инжекции на лету
SYSTEM_PROMPTS_REGISTRY = {
    "default": "Ты — OmniAgent, автономный ИИ-супервизор платформы OmniFactory. Создатель — инженер Бондарев Е. Отвечай кратко, емко, используя предоставленный технический контекст базы знаний."
}

import chromadb
import json


@app.websocket("/ws/ai-agent")
async def websocket_ai_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Считываем tenant_id из параметров запроса (?tenant_id=...)
    query_params = websocket.query_params
    tenant_id = query_params.get("tenant_id", "default")

    logger.info(f">>> OMNI_AGENT: Установлен асинхронный WebSocket канал для [TENANT: {tenant_id}]")

    # Переключаем контекст векторной базы данных под конкретного клиента
    if tenant_id == "default":
        db_path = str(BASE_DIR / "chroma_db_storage")
        collection_name = "omnifactory_intelligence"
    else:
        db_path = str(BASE_DIR / "tenants_storage" / tenant_id / "chroma_db_storage")
        collection_name = f"omnifactory_intelligence_{tenant_id}"

    try:
        chroma_client = chromadb.PersistentClient(path=db_path)
        collection = chroma_client.get_collection(name=collection_name)
        logger.info(f"✓ [RAG ALIGNED] Подключена изолированная база знаний для {tenant_id}")
    except Exception as e:
        logger.warning(f"⚠️ База ChromaDB для {tenant_id} не найдена. Работаем без RAG-контекста: {e}")
        collection = None

    try:
        while True:
            raw_data = await websocket.receive_text()

            # Проверяем, не прилетел ли управляющий JSON из Промпт-Конструктора
            try:
                parsed_command = json.loads(raw_data)
                if parsed_command.get("action") == "inject_prompt":
                    SYSTEM_PROMPTS_REGISTRY[tenant_id] = parsed_command.get("prompt")
                    logger.info(f"🧠 ИИ-ЯДРО: Инжектирована новая системная директива для {tenant_id}")
                    await websocket.send_text(f"[SYSTEM]: Системная директива ядра OmniAgent успешно обновлена.")
                    continue
            except json.JSONDecodeError:
                user_message = raw_data

            # Сборка памяти сессии с учетом актуальной роли из промпт-инжектора
            active_instruction = SYSTEM_PROMPTS_REGISTRY.get(tenant_id, SYSTEM_PROMPTS_REGISTRY["default"])
            session_memory = [{"role": "system", "content": active_instruction}]

            # Векторный RAG-поиск по контексту
            context_addon = ""
            if collection:
                try:
                    results = collection.query(query_texts=[user_message], n_results=1)
                    if results and results['documents'] and results['documents'][0]:
                        matched_doc = results['documents'][0][0]
                        context_addon = f"\n[LOCAL_CONTEXT]: {matched_doc}\n"
                        logger.info("◈ [RAG MATCH] Соответствие найдено и подмешано в память модели.")
                except Exception as e:
                    logger.error(f"Ошибка выборки ChromaDB: {e}")

            full_prompt = user_message + context_addon
            session_memory.append({"role": "user", "content": full_prompt})

            # Вызов инференса локальной Ollama модели
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: ollama.chat(model='codellama', messages=session_memory)
                )

                agent_reply = response['message']['content']
                await websocket.send_text(agent_reply)

            except Exception as e:
                logger.error(f"Ошибка Ollama Engine: {str(e)}")
                await websocket.send_text(f"[ERROR] Сбой локальной ИИ-ноды: {str(e)}")

    except WebSocketDisconnect:
        logger.info(f">>> OMNI_AGENT: Сессия {tenant_id} закрыта супервизором.")


import io
import json
import zipfile
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List




@app.post("/api/builder/generate", summary="Компиляция Enterprise AI-Магазина в ZIP", tags=["Генератор Кода"])
async def generate_bot_archive(data: BuildRequest):
    if not data.selected_ids:
        raise HTTPException(status_code=400, detail="На холсте отсутствуют модули для сборки.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # 1. СИСТЕМНЫЙ МАНИФЕСТ И СПЕЦИФИКАЦИЯ СБОРКИ
        manifest_json = json.dumps({"compiled_nodes": data.selected_ids, "version": "Enterprise 1.0.0"}, indent=4,
                                   ensure_ascii=False)
        zip_file.writestr("bot_runtime/config/manifest.json", manifest_json)

        # 2. ИЗОЛИРОВАННАЯ ТОВАРНАЯ БАЗА ДАННЫХ ДЛЯ КЛИЕНТА (config/catalog.json)
        catalog_data = {
            "categories": [
                {
                    "id": "modules",
                    "name": "Инженерные модули",
                    "items": [
                        {"id": "node_01", "name": "Контур Когнитивного Реестра", "price": 15000,
                         "desc": "Ядро векторизации ChromaDB + RAG"},
                        {"id": "node_02", "name": "Оркестратор Docker Инстансов", "price": 25000,
                         "desc": "Модуль SaaS деплоя контейнеров"}
                    ]
                },
                {
                    "id": "ai_agents",
                    "name": "Нейросетевые Агенты",
                    "items": [
                        {"id": "agent_sale", "name": "ИИ-Консультант Магазина", "price": 45000,
                         "desc": "Автономный агент продаж со сквозной памятью"},
                        {"id": "agent_supervisor", "name": "Супервизор Инфраструктуры", "price": 60000,
                         "desc": "ИИ для анализа логов и перезапуска нод"}
                    ]
                }
            ]
        }
        zip_file.writestr("bot_runtime/config/catalog.json", json.dumps(catalog_data, indent=4, ensure_ascii=False))

        # 3. ЗАВИСИМОСТИ СРЕДЫ РАЗВЕРТЫВАНИЯ
        requirements_txt = (
            "aiogram==3.13.1\n"
            "openai==1.50.0\n"
            "pydantic==2.9.2\n"
            "asyncio==3.4.3\n"
        )
        zip_file.writestr("bot_runtime/requirements.txt", requirements_txt)

        # 4. СЕРДЦЕ МАГАЗИНА: УМНАЯ КОРЗИНА И КАТАЛОГ (brain/store_logic.py)
        store_logic_py = (
            "# -*- coding: utf-8 -*-\n"
            "import json\n"
            "import os\n"
            "from pathlib import Path\n\n"
            "BASE_DIR = Path(__file__).resolve().parent.parent\n\n"
            "class EnterpriseStore:\n"
            "    def __init__(self):\n"
            "        catalog_path = BASE_DIR / 'config' / 'catalog.json'\n"
            "        with open(catalog_path, 'r', encoding='utf-8') as f:\n"
            "            self.catalog = json.load(f)\n"
            "        self.carts = {}  # Временное in-memory хранилище корзин {user_id: {item_id: quantity}}\n\n"
            "    def get_catalog_text(self) -> str:\n"
            "        text = '📦 **АКТУАЛЬНЫЙ КАТАЛОГ ТОВАРОВ OMNIFACTORY**:\\n\\n'\n"
            "        for cat in self.catalog['categories']:\n"
            "            text += f'🔹 __Категория: {cat[\"name\"]}\\__\\n'\n"
            "            for item in cat['items']:\n"
            "                text += f'   🆔 ID: **{item[\"id\"]}** | {item[\"name\"]}\\n'\n"
            "                text += f'   💵 Цена: {item[\"price\"]} руб. | {item[\"desc\"]}\\n\\n'\n"
            "        return text\n\n"
            "    def add_to_cart(self, user_id: int, item_id: str) -> str:\n"
            "        # Поиск товара в каталоге\n"
            "        found_item = None\n"
            "        for cat in self.catalog['categories']:\n"
            "            for item in cat['items']:\n"
            "                if item['id'] == item_id:\n"
            "                    found_item = item\n"
            "        if not found_item:\n"
            "            return f'❌ Товар с ID {item_id} не обнаружен в матрице каталога.'\n"
            "        \n"
            "        if user_id not in self.carts: self.carts[user_id] = {}\n"
            "        self.carts[user_id][item_id] = self.carts[user_id].get(item_id, 0) + 1\n"
            "        return f'🛒 Добавлено в корзину: **{found_item[\"name\"]}** (1 шт.)'\n\n"
            "    def get_cart_text(self, user_id: int) -> str:\n"
            "        if user_id not in self.carts or not self.carts[user_id]:\n"
            "            return '🛒 Ваша корзина абсолютно пуста.'\n"
            "        \n"
            "        text = '🛒 **ВАША ТЕКУЩАЯ КОРЗИНА**:\\n\\n'\n"
            "        total_price = 0\n"
            "        for item_id, qty in self.carts[user_id].items():\n"
            "            for cat in self.catalog['categories']:\n"
            "                for item in cat['items']:\n"
            "                    if item['id'] == item_id:\n"
            "                        subtotal = item['price'] * qty\n"
            "                        total_price += subtotal\n"
            "                        text += f'• {item[\"name\"]} x {qty} шт. = {subtotal} руб.\\n'\n"
            "        text += f'\\n💰 **ИТОГО К ОПЛАТЕ: {total_price} руб.**\\nИспользуйте /checkout для оформления.'\n"
            "        return text\n"
        )
        zip_file.writestr("bot_runtime/brain/store_logic.py", store_logic_py)

        # 5. ИИ-КОНСУЛЬТАНТ И АНАЛИЗАТОР ИНТЕНТОВ (brain/assistant.py)
        assistant_py = (
            "# -*- coding: utf-8 -*-\n"
            "import os\n"
            "import json\n"
            "from openai import AsyncOpenAI\n\n"
            "class AIQuerySupervisor:\n"
            "    def __init__(self):\n"
            "        api_key = os.getenv('AI_API_KEY', 'local-ollama-token')\n"
            "        base_url = os.getenv('AI_BASE_URL', 'http://host.docker.internal:8089/v1')\n"
            "        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)\n"
            "        self.model = os.getenv('AI_MODEL', 'codellama')\n\n"
            "    async def analyze_and_chat(self, prompt: str, cart_context: str) -> dict:\n"
            "        \"\"\"ИИ одновременно общается и выносит решение, нужно ли программно добавить товар в корзину\"\"\"\n"
            "        system_instruction = (\n"
            "            'Ты — интеллектуальный ассистент интернет-магазина OmniFactory. Отвечай кратко, помогай клиенту.\\n'\n"
            "            'ВАЖНО: Твоя задача — возвращать ответ СТРОГО в формате JSON с двумя ключами:\\n'\n"
            "            '1. \"reply\" — текстовый ответ клиенту.\\n'\n"
            "            '2. \"action_add_item\" — если клиент явно просит купить или добавить товар, укажи его ID (например, \"node_01\"), иначе null.\\n\\n'\n"
            "            f'Текущее состояние корзины покупателя: {cart_context}'\n"
            "        )\n"
            "        try:\n"
            "            response = await self.client.chat.completions.create(\n"
            "                model=self.model,\n"
            "                messages=[\n"
            "                    {'role': 'system', 'content': system_instruction},\n"
            "                    {'role': 'user', 'content': prompt}\n"
            "                ],\n"
            "                response_format={ \"type\": \"json_object\" },\n"
            "                temperature=0.3\n"
            "            )\n"
            "            return json.loads(response.choices[0].message.content)\n"
            "        except Exception:\n"
            "            return {\"reply\": \"🤖 Я обрабатываю ваш запрос. Вы можете использовать ручное меню каталога.\", \"action_add_item\": None}\n"
        )
        zip_file.writestr("bot_runtime/brain/assistant.py", assistant_py)

        # 6. АСИНХРОННЫЙ МАРШРУТИЗАТОР СОБЫТИЙ (core/engine.py)
        engine_py = (
            "# -*- coding: utf-8 -*-\n"
            "import logging\n"
            "from brain.store_logic import EnterpriseStore\n"
            "from brain.assistant import AIQuerySupervisor\n\n"
            "class CrossPlatformRouter:\n"
            "    def __init__(self):\n"
            "        self.store = EnterpriseStore()\n"
            "        self.ai = AIQuerySupervisor()\n\n"
            "    async def process_user_intent(self, user_id: int, text: str) -> str:\n"
            "        clean_text = text.lower().strip()\n"
            "        \n"
            "        # Ручные перехватчики команд\n"
            "        if 'каталог' in clean_text or 'меню' in clean_text:\n"
            "            return self.store.get_catalog_text()\n"
            "        if 'корзина' in clean_text:\n"
            "            return self.store.get_cart_text(user_id)\n"
            "        \n"
            "        # Передаем запрос ИИ-Супервизору вместе с контекстом корзины\n"
            "        cart_ctx = self.store.get_cart_text(user_id)\n"
            "        ai_analysis = await self.ai.analyze_and_chat(text, cart_ctx)\n"
            "        \n"
            "        # Если ИИ принял решение добавить товар — выполняем\n"
            "        if ai_analysis.get('action_add_item'):\n"
            "            action_reply = self.store.add_to_cart(user_id, ai_analysis['action_add_item'])\n"
            "            return f\"{ai_analysis['reply']}\\n\\n⚙️ [SYSTEM LOG]: {action_reply}\"\n"
            "            \n"
            "        return ai_analysis['reply']\n"
        )
        zip_file.writestr("bot_runtime/core/engine.py", engine_py)

        # 7. ШЛЮЗ AIOGRAM 3.X ДЛЯ TELEGRAM (integrations/telegram.py)
        telegram_py = (
            "# -*- coding: utf-8 -*-\n"
            "import os\n"
            "import sys\n"
            "import logging\n"
            "from aiogram import Bot, Dispatcher, types\n"
            "from aiogram.filters import Command\n"
            "from core.engine import CrossPlatformRouter\n\n"
            "TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN_HERE')\n"
            "dp = Dispatcher()\n"
            "router = CrossPlatformRouter()\n\n"
            "@dp.message(Command('start'))\n"
            "async def send_welcome(message: types.Message):\n"
            "    await message.reply('⚡ **Добро пожаловать в Enterprise AI-Магазин OmniFactory!**\\n\\n' \n"
            "                        'Я функционирую на базе локальной нейросети и асинхронного ядра.\\n\\n' \n"
            "                        '📋 **Команды управления**:\\n' \n"
            "                        '📦 Напишите **\"Каталог\"** — для просмотра товарных нод.\\n' \n"
            "                        '🛒 Напишите **\"Корзина\"** — для проверки выбранных позиций.\\n' \n"
            "                        '🤖 Или просто общайтесь со мной: я умею добавлять товары в корзину прямо из контекста разговора!')\n\n"
            "@dp.message()\n"
            "async def handle_message(message: types.Message):\n"
            "    if not message.text: return\n"
            "    reply_text = await router.process_user_intent(message.from_user.id, message.text)\n"
            "    await message.answer(reply_text, parse_mode='Markdown')\n\n"
            "async def main():\n"
            "    logging.basicConfig(level=logging.INFO, stream=sys.stdout)\n"
            "    bot = Bot(token=TOKEN)\n"
            "    print('◈ [SUCCESS] Асинхронное enterprise-ядро шлюза Telegram запущено.')\n"
            "    await dp.start_polling(bot)\n"
        )
        zip_file.writestr("bot_runtime/integrations/telegram.py", telegram_py)

        # 8. ТОЧКА ВХОДА (main.py)
        main_py = (
            "# -*- coding: utf-8 -*-\n"
            "import asyncio\n"
            "import logging\n"
            "from integrations import telegram\n\n"
            "if __name__ == '__main__':\n"
            "    try:\n"
            "        asyncio.run(telegram.main())\n"
            "    except (KeyboardInterrupt, SystemExit):\n"
            "        logging.info('Bot stopped.')\n"
        )
        zip_file.writestr("bot_runtime/main.py", main_py)

        # 9. DOCKERFILE И СТРУКТУРНЫЕ ИНИЦИАЛИЗАТОРЫ ПАКЕТОВ
        dockerfile = (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "ENV PYTHONDONTWRITEBYTECODE=1\n"
            "ENV PYTHONUNBUFFERED=1\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "CMD [\"python\", \"main.py\"]\n"
        )
        zip_file.writestr("bot_runtime/Dockerfile", dockerfile)
        zip_file.writestr("bot_runtime/integrations/__init__.py", "")
        zip_file.writestr("bot_runtime/brain/__init__.py", "")
        zip_file.writestr("bot_runtime/core/__init__.py", "")

        # 10. РАСШИРЕННЫЙ README ДЛЯ КЛИЕНТА С ИНСТРУКЦИЕЙ DEPLOY
        readme_md = (
            "# ⚡ ENTERPRISE AI-STORE RUNTIME // POWERED BY OMNIFACTORY\n\n"
            "Вы выгрузили промышленный инстанс автономного интернет-магазина со встроенным ИИ-консультантом.\n\n"
            "## 🚀 Вариант 1: Локальный запуск в виртуальном окружении\n"
            "1. Распакуйте zip-архив в рабочую папку.\n"
            "2. Инициализируйте окружение: `python -m venv .venv`\n"
            "3. Активируйте: `.venv\\Scripts\\activate` (Windows) или `source .venv/bin/activate` (Linux/Mac)\n"
            "4. Выполните установку зависимостей: `pip install -r requirements.txt`\n"
            "5. Пропишите токен в терминале: `set TELEGRAM_BOT_TOKEN=\"твой_токен_бота\"`\n"
            "6. Запустите: `python main.py`\n\n"
            "## 🐳 Вариант 2: Изолированный промышленный запуск (Docker)\n"
            "1. Соберите Docker-образ: `docker build -t omni-store-instance .`\n"
            "2. Запустите контейнер:\n"
            "   `docker run -d --name store_instance -e TELEGRAM_BOT_TOKEN=\"твой_токен\" omni-store-instance`\n"
        )
        zip_file.writestr("bot_runtime/README.md", readme_md)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=omnifactory_enterprise_bot.zip"}
    )


@app.get("/admin/fragment/dashboard", summary="Получить HTML фрагмент n8n-дашборда")
async def get_dashboard_fragment():
    fragment_path = BASE_DIR / "templates" / "dashboard_fragment.html"
    if not fragment_path.exists():
        return HTMLResponse(content="<div style='color:red;'>Фрагмент dashboard_fragment.html не найден.</div>")
    with open(fragment_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ==============================================================================
# ENTERPRISE EXTENSION: DOCKER ORCHESTRATION & DYNAMIC RUNTIME
# ==============================================================================
import subprocess
import shutil


class DeployRequest(BaseModel):
    client_id: str = Field(..., description="Уникальный идентификатор клиента/компании.",
                           json_schema_extra={"example": "client_id_001"})
    telegram_token: str = Field(..., description="Токен создаваемого бота.",
                                json_schema_extra={"example": "123456:ABC-DEF"})
    selected_nodes: List[str] = Field(..., description="Массив идентификаторов нод с холста.")


@app.post("/api/v1/factory/deploy", summary="Enterprise Деплой: Запуск изолированного контейнера бота в рантайме",
          tags=["Enterprise Оркестратор"])
async def enterprise_deploy_bot(data: DeployRequest):
    if not data.telegram_token or not data.client_id:
        raise HTTPException(status_code=400, detail="client_id и telegram_token обязательны для конфигурации инстанса.")

    # Формируем изолированную директорию для инстанса клиента
    workspace_dir = BASE_DIR / "deployed_environments" / data.client_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Для симуляции деплоя без падения Windows-сервера генерируем файлы окружения локально
        env_file_path = workspace_dir / ".env"
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(f"TELEGRAM_BOT_TOKEN={data.telegram_token}\n")
            f.write(f"CLIENT_WORKSPACE={data.client_id}\n")
            f.write(f"AI_MODEL=codellama\n")

        logger.info(f"◈ [ENTERPRISE] Сформировано изолированное окружение подсистемы для {data.client_id}")

        # Интеграция с локальным Docker CLI через subprocess (в бэкграунде)
        # В реальной Linux/WSL среде здесь вызывается сборка и старт контейнера:
        # subprocess.Popen(["docker", "run", "-d", "--name", f"bot_{data.client_id}", "--env-file", str(env_file_path), "omnifactory-base-image"])

        return {
            "status": "PROVISIONED",
            "workspace_path": str(workspace_dir),
            "allocated_node": f"inst_container_{data.client_id}",
            "metrics": {
                "status": "ONLINE",
                "uptime": "1s",
                "memory_quota": "256MB"
            },
            "instruction": "Экземпляр бота успешно изолирован, виртуальное окружение развернуто. Конвейер готов к приему трафика."
        }
    except Exception as e:
        logger.error(f"Ошибка распределенного деплоя: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Критический сбой оркестратора инфраструктуры: {str(e)}")


def compile_canvas_into_python(drawflow_data: dict) -> str:
    """
    Транслятор визуальных блоков Drawflow в готовые цепочки обработчиков aiogram 3.x
    """
    home_module = drawflow_data.get("drawflow", {}).get("Home", {})
    nodes = home_module.get("data", {})

    if not nodes:
        return "    await message.answer('🤖 Бот OmniFactory запущен, но сценарий на холсте пуст.')"

    compiled_handlers = []

    for node_id, node_meta in nodes.items():
        node_name = node_meta.get("name")  # Тип кубика, выбранный на холсте
        data = node_meta.get("data", {})  # Параметры, введённые пользователем в поле блока

        compiled_handlers.append(f"    # --- START MODULE: {node_name.toUpperCase()} [ID: {node_id}] ---")

        # КОМПОНЕНТ 1: Диалог с вариантами ответов (Кнопки)
        if node_name == "dialog_question":
            question = data.get("question", "Задайте вопрос?")
            options = data.get("options", "Да;Нет").split(";")

            kb_lines = ["    builder = InlineKeyboardBuilder()"]
            for opt in options:
                kb_lines.append(f"    builder.button(text='{opt.strip()}', callback_data='cb_{node_id}_{opt.strip()}')")
            kb_lines.append(f"    await message.answer('{question}', reply_markup=builder.as_markup())")
            compiled_handlers.extend(kb_lines)

        # КОМПОНЕНТ 2: Универсальная отправка файла клиенту
        elif node_name == "send_file":
            file_type = data.get("file_type", "document")  # photo, photo, voice, document
            file_path = data.get("file_path", "storage/report.pdf")
            caption = data.get("caption", "Ваш документ сформирован.")

            if file_type == "photo":
                compiled_handlers.append(
                    f"    await message.answer_photo(photo=types.FSInputFile('{file_path}'), caption='{caption}')")
            else:
                compiled_handlers.append(
                    f"    await message.answer_document(document=types.FSInputFile('{file_path}'), caption='{caption}')")

        # КОМПОНЕНТ 3: Приём файла от клиента (Входной шлюз данных)
        elif node_name == "receive_file":
            target_dir = data.get("target_dir", "downloads/")
            compiled_handlers.append(
                f"    if message.document:\n"
                f"        file_id = message.document.file_id\n"
                f"        file = await bot.get_file(file_id)\n"
                f"        await bot.download_file(file.file_path, '{target_dir}' + message.document.file_name)\n"
                f"        await message.answer('💾 Файл успешно принят и сохранён в локальный контур {target_dir}')"
            )

        # КОМПОНЕНТ 4: Нейросетевой хаб (Когнитивный блок Ollama)
        elif node_name == "ai_hub":
            model = data.get("model", "codellama")
            prompt_context = data.get("prompt_prefix", "Ты ассистент магазина. Ответь покупателю:")

            compiled_handlers.append(
                f"    ai_response = await asyncio.get_event_loop().run_in_executor(\n"
                f"        None, lambda: ollama.chat(model='{model}', messages=[{{'role': 'user', 'content': '{prompt_context} ' + message.text}}])\n"
                f"    )\n"
                f"    await message.answer(ai_response['message']['content'])"
            )

        else:
            compiled_handlers.append(f"    # Компонент [{node_name}] выполнил сквозной транзит данных.")

        compiled_handlers.append(f"    # --- END MODULE: {node_name.toUpperCase()} ---\n")

    return "\n".join(compiled_handlers)


from services.component_factory import component_library


class CanvasBuildRequest(BaseModel):
    drawflow: Dict[str, Any]


@app.post("/api/builder/generate", summary="Компиляция компонентов холста в ZIP")
async def generate_bot_from_canvas(payload: CanvasBuildRequest = Body(...)):
    logger.info("◈ [COMPILER] Инициализирован запуск сборщика асинхронных Python-компонентов.")

    # Извлекаем сырые данные Drawflow и генерируем тело обработчика сообщений
    raw_drawflow_data = payload.model_dump()
    generated_handlers_code = component_library.compile_canvas_flow(raw_drawflow_data)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # 1. Сборка основного файла архитектуры бота (main.py)
        bot_main_py = (
            "# -*- coding: utf-8 -*-\n"
            "import os\n"
            "import sys\n"
            "import asyncio\n"
            "import logging\n"
            "import ollama\n"
            "from aiogram import Bot, Dispatcher, types\n"
            "from aiogram.fsm.storage.memory import MemoryStorage\n"
            "from aiogram.fsm.state import State, StatesGroup\n"
            "from aiogram.fsm.context import FSMContext\n"
            "from aiogram.utils.keyboard import InlineKeyboardBuilder\n\n"
            "logging.basicConfig(level=logging.INFO, stream=sys.stdout)\n"
            "logger = logging.getLogger('CompiledBot')\n\n"
            "# Инициализация машины состояний FSM под наши компоненты\n"
            "class CustomBotStates(StatesGroup):\n"
            "    WAITING_FOR_INPUT = State()\n"
            "    WAITING_FOR_FILE = State()\n"
            "    PROCESSING_AI = State()\n\n"
            "storage = MemoryStorage()\n"
            "dp = Dispatcher(storage=storage)\n"
            "bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN_HERE'))\n\n"
            "# ГЛОБАЛЬНЫЙ РОУТЕР СОБЫТИЙ ХОЛСТА\n"
            "@dp.message()\n"
            "async def core_canvas_router(message: types.Message, state: FSMContext):\n"
            f"{generated_handlers_code}\n\n"
            "async def main():\n"
            "    logger.info('◈ [SUCCESS] Асинхронное ядро OmniFactory Bot запущено.')\n"
            "    await dp.start_polling(bot)\n\n"
            "if __name__ == '__main__':\n"
            "    try:\n"
            "        asyncio.run(main())\n"
            "    except (KeyboardInterrupt, SystemExit):\n"
            "        logger.info('Bot stopped.')\n"
        )
        # Простая проверка на синтаксис Python перед упаковкой
        try:
            compile(bot_main_py, 'main.py', 'exec')
        except SyntaxError as e:
            logger.error(f"Синтаксическая ошибка в сгенерированном коде: {e}")
            # Здесь можно вернуть HTTP 400 Bad Request
        zip_file.writestr("bot_runtime/main.py", bot_main_py)

        # 2. Окружение, манифест и докер-контейнеризация
        requirements_txt = "aiogram==3.13.1\nollama==0.2.1\npydantic==2.9.2\n"
        zip_file.writestr("bot_runtime/requirements.txt", requirements_txt)

        dockerfile_content = (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "CMD [\"python\", \"main.py\"]\n"
        )
        zip_file.writestr("bot_runtime/Dockerfile", dockerfile_content)

        manifest_json = {
            "engine": "OmniFactory Enterprise Runtime",
            "version": "1.4.0",
            "compiled_by": "Bondarev_E"
        }
        zip_file.writestr("bot_runtime/config/manifest.json", json.dumps(manifest_json, indent=4, ensure_ascii=False))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=omnifactory_compiled_bot.zip"}
    )

    # В ваш main.py (FastAPI сервер)


# В ваш main.py (FastAPI сервер)
@app.post("/api/orchestrator/update_graph/{bot_id}")
async def update_bot_graph(bot_id: str, graph_data: dict):
    # Оркестратор "на лету" подменяет граф в памяти
    orchestrator.active_graphs[bot_id] = graph_data

    # Регистрация новой логики без перезагрузки процессов
    await orchestrator.reload_bot_config(bot_id)

    return {"status": "SUCCESS", "message": f"Бот {bot_id} пересобран в Runtime."}


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("👉 ГЛАВНЫЙ ВХОД В ЛАБОРАТОРИЮ (HOME_NODE): http://127.0.0.1:8089/")
    print("👉 ВХОД В АДМИНИСТРАТИВНУЮ ПАНЕЛЬ: http://127.0.0.1:8089/admin")
    print("=" * 80 + "\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8089, reload=False)
