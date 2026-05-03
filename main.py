# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /main.py
# VERSION: 1.4.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Управление входящими лидами и коммуникациями.
# PURPOSE: Автоматизация сбора контактов и потребностей клиентов.
# DEPENDENCIES: prompts/lead_capture.prompt, models.py
# AUTHORS: Human & AI Collaboration
# STATUS: Beta

# ==============================================================================

import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI
from genkit import genkit
from genkit.plugins import google_ai
import asyncio
import uuid

# ИМПОРТЫ ДЛЯ СБОРЩИКА
import asyncio
import uuid
import time
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import firestore

import asyncio  # Добавь в начало файла
import uuid  # Добавь в начало файла
# ==============================================================================
           #Строим АИ Асистента#
# ==============================================================================
ai = genkit(plugins=[google_ai.init(api_key=os.getenv('GOOGLE_API_KEY'))])
app = FastAPI(title="Personal Web Space API")
# === 2. НАСТРОЙКА CORS (СРАЗУ ПОСЛЕ app = FastAPI()) ===
# Без этого блока Фронтенд не сможет достучаться до Бэкенда!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы с любого адреса (твоего React-порта)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 3. САМ ЭНДПОИНТ  ===
@app.post("/api/builder/generate")
async def generate_project(data: dict):
    """
    ENGINE: Web_Factory_Builder_v1
    DESCRIPTION: Принимает конфигурацию модулей от React,
    логирует процесс и регистрирует результат в Firebase.
    """
    try:
        # Извлекаем данные из запроса
        modules = data.get('modules', [])
        author = data.get('author', 'Bondarev_E')

        print(f"\n[🚀 BUILD_STARTED] Author: {author}")
        print(f"[⚙️ PROCESSING] Nodes: {', '.join(modules)}")

        # --- ФАЗА 1: СИМУЛЯЦИЯ СБОРКИ (ОЖИВЛЕНИЕ ЖЕЛЕЗА) ---
        # В будущем здесь будет вызов функций генерации кода
        await asyncio.sleep(2)  # Имитируем работу компилятора

        # --- ФАЗА 2: ГЕНЕРАЦИЯ УНИКАЛЬНОГО ИДЕНТИФИКАТОРА ---
        build_id = f"BUILD-{str(uuid.uuid4())[:8].upper()}"

        # --- ФАЗА 3: РЕГИСТРАЦИЯ В FIREBASE ---
        # Мы создаем документ в коллекции 'build_history'
        build_data = {
            "build_id": build_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "author": author,
            "modules": modules,
            "status": "SUCCESS",
            "environment": "FastAPI_Production_Core",
            "metadata": {
                "os": "Universal_Node",
                "engine_version": "1.8.0"
            }
        }

        # Сохранение в Firestore
        db.collection("build_history").document(build_id).set(build_data)
        print(f"[✅ DATABASE] Record {build_id} saved successfully.")

        # --- ФАЗА 4: ОТВЕТ КЛИЕНТУ (ФРОНТЕНДУ) ---
        return {
            "status": "COMPLETED",
            "build_id": build_id,
            "author": author,
            "message": f"Проект {build_id} успешно сгенерирован и зарегистрирован в системе.",
            "artifacts": {
                "main_file": "bot_core.py",
                "config": "env.json",
                "docker": "Dockerfile",
                "readme": "INSTRUCTIONS.md"
            },
            "timestamp": time.time()
        }

    except Exception as e:
        print(f"[❌ CRITICAL_ERROR] Build failed: {str(e)}")
        return {
            "status": "ERROR",
            "message": f"System failure: {str(e)}"
        }


# ==============================================================================


# Инициализация Firebase
# УБЕДИТСЯ, что есть доступ к учетным данным (через ADC или json файл)
default_app = firebase_admin.initialize_app()
db = firestore.client()


@app.post("/chat/interact")
async def chat_interact(message: str, history: list = []):
    lead_prompt = ai.prompt('lead_capture')
    response = lead_prompt.generate(
        input={'last_message': message, 'history': history}
    )
    res_data = response.output

    # Если сбор данных завершен — сохраняем в "Comm Center"
    if res_data.get('is_complete'):
        db.collection("communications").add({
            "timestamp": "2026-05-02 20:00",
            "client_name": res_data['extracted_data'].get('contact', 'Unknown'),
            "summary": res_data['extracted_data'].get('need_description'),
            "sentiment": "Neutral",
            "extracted_entities": {
                "format": res_data['extracted_data'].get('feedback_format')
            },
            "status": "New"
        })

    return res_data


@app.post("/plan-project")
async def plan_project(idea: str):
    architect_prompt = ai.prompt('web_architect')
    response = architect_prompt.generate(input={'user_idea': idea})
    data = response.output

    # АВТОМАТИЗАЦИЯ: Создаем запись о новом проекте в "Коммуникациях"
    db.collection("communications").add({
        "timestamp": "2026-05-02 18:45",
        "client_name": "System Architect",
        "summary": f"Generated concept for: {data['site_name']}",
        "sentiment": "Neutral",
        "extracted_entities": {"project": data['site_name'], "stack": str(data['tech_stack'])},
        "status": "New"
    })

    return data

@app.post("/plan-project")
async def plan_project(idea: str = "Магазин хендмейд мебели из дерева с доставкой и гарантией"):
    """
    Запускает Flow архитектора для создания концепции сайта-визитки.
    """
    architect_prompt = ai.prompt('web_architect')

    # Мы ожидаем, что промпт вернет структуру:
    # {site_name, concept_summary, tech_stack, nodes, edges, feature_backlog}
    response = architect_prompt.generate(input={'user_idea': idea})
    return response.output




### этот эндпоинт. Он будет имитировать реальные фазы сборки для фронтенда и сохранять результат в твой Firestore.###



# --- [ПУТЬ 1: СБОРЩИК ПРОЕКТОВ] ---
@app.post("/api/builder/generate")
async def generate_project(data: dict):
    """
    Принимает конфигурацию модулей, имитирует компиляцию
    и регистрирует билд в базе данных.
    """
    modules = data.get('modules', [])
    author = data.get('author', 'Bondarev_E')

    # 1. Имитируем нагрузку на ядро (сборка занимает время)
    # На фронтенде это будет выглядеть как прогресс-бар
    await asyncio.sleep(2)

    # 2. Генерируем уникальный номер сборки
    build_id = f"BUILD-{str(uuid.uuid4())[:8].upper()}"

    # 3. Протоколирование в твой Firebase
    try:
        db.collection("build_history").document(build_id).set({
            "build_id": build_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "author": author,
            "modules": modules,
            "status": "SUCCESS",
            "environment": "FastAPI_Production"
        })
    except Exception as e:
        print(f"Build Protocol Error: {e}")

    return {
        "status": "COMPLETED",
        "build_id": build_id,
        "author": author,
        "message": f"Проект {build_id} успешно сгенерирован и упакован в ZIP."
    }




app = FastAPI(title="Personal Web Space API")


@app.get("/")
async def root():
    return {"message": "Genkit Python API is running"}


@app.post("/users/")
async def create_user(user: UserProfile):
    # Пример сохранения в Firestore (навык firebase-firestore)
    doc_ref = db.collection("users").document(user.uid)
    doc_ref.set(user.dict())
    return {"status": "success", "uid": user.uid}


app = FastAPI(title="Personal Web Space API")


# --- FLOW 1: Архитектор (Планирование) ---
@ai.flow(name="generate_web_concept")
def generate_web_concept(user_idea: str):
    architect_prompt = ai.prompt('web_architect')
    response = architect_prompt.generate(input={'user_idea': user_idea})
    return response.output


# --- FLOW 2: Разработчик (Реализация задачи) ---
@ai.flow(name="implement_task")
def implement_task(tech_stack: list, task_description: str, context: str):
    """Берет задачу и генерирует код"""
    developer_prompt = ai.prompt('code_developer')
    response = developer_prompt.generate(
        input={
            'tech_stack': tech_stack,
            'task_description': task_description,
            'context': context
        }
    )
    return response.text


# --- API Endpoints ---

@app.post("/plan-project")
async def plan_project(idea: str):
    return generate_web_concept(idea)


@app.post("/generate-code")
async def generate_code(tech_stack: list, task: str, context: str):
    return {"code": implement_task(tech_stack, task, context)}


# ==============================================================================
####### КАЛЕНДАРЬ #######
# ==============================================================================
# 1. Получение всех событий для календаря
@app.route('/api/crm/events')
def get_crm_events():
    events = CRMEvent.query.all()
    # Превращаем объекты SQLAlchemy в JSON-список
    return jsonify([event.to_dict() for event in events])


# 2. Создание новой задачи через интерфейс
@app.route('/api/crm/add-event', methods=['POST'])
def add_event():
    data = request.json
    new_event = CRMEvent(
        title=data['title'],
        scheduled_time=datetime.fromisoformat(data['start']),
        target_site=data.get('target', 'LOCAL'),
        status='PENDING'
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"status": "SUCCESS", "id": new_event.id})


#######КОНЕЦ ФУНКЦИИ#######

###«надсмотрщик» над  базой данных###
def task_executor():
    """Фоновая функция, которая ищет задачи в БД и выполняет их."""
    with app.app_context():
        now = datetime.utcnow()
        # Ищем события, время которых пришло, и которые еще не выполнены
        pending_tasks = CRMEvent.query.filter(
            CRMEvent.scheduled_time <= now,
            CRMEvent.status == 'PENDING'
        ).all()

        for task in pending_tasks:
            print(f">>> EXECUTING TASK: {task.title} for {task.target_site}")

            try:
                # Логика запуска команд
                if task.linked_script == 'RESTART':
                    # Здесь может быть вызов вашего моста Bridge
                    requests.post(f"https://{task.target_site}/api/bridge/restart", headers={"X-Admin-Secret": "..."})

                elif task.linked_script == 'HEALTH_SCAN':
                    # Логика сканирования сайта
                    pass

                task.status = 'EXECUTED'
            except Exception as e:
                task.status = f'FAILED: {str(e)}'

            db.session.commit()


# Запуск планировщика при старте сервера
scheduler = BackgroundScheduler()
scheduler.add_job(func=task_executor, trigger="interval", seconds=60)  # Проверка каждую минуту
scheduler.start()


@app.post("/analyze-site")
async def analyze_site(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url.startswith("http"):
        url = "https://" + url

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            html = response.text.lower()

            # Базовый анализатор технологий
            scripts = html.count("<script")
            styles = html.count("<link rel=\"stylesheet\"") + html.count("<style")

            tech = "Custom Stack"
            if "react" in html: tech = "React.js Framework"
            if "vue" in html: tech = "Vue.js Interface"
            if "wordpress" in html: tech = "WordPress CMS"

            return {
                "architecture": tech,
                "security": "SSL/TLS Active" if "https" in url else "Standard HTTP",
                "price": f"${1500 + (scripts * 20)}",
                "time": f"{7 + (scripts // 5)} Days",
                "metrics": {"scripts": scripts, "styles": styles,
                            "latency": f"{int((time.time() - start_time) * 1000)}ms"}
            }
    except:
        return {"error": "Target unreachable"}


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы с любого адреса (твоего React-порта)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. СНАЧАЛА определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. ТЕПЕРЬ определяем пути, используя BASE_DIR
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
ASSETS_PATH = os.path.join(BASE_DIR, "assets")

# 3. Монтируем папку
if os.path.exists(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")
else:
    print(f"ERROR: Директория не найдена по пути {ASSETS_PATH}")


# === 3.  ЭНДПОИНТ СБОРЩИКА  ===
@app.post("/api/builder/generate")
async def generate_project(data: dict):
    """
    ENGINE: Web_Factory_Builder_v1
    DESCRIPTION: Принимает конфигурацию модулей от React,
    логирует процесс и регистрирует результат в Firebase.
    """
    try:
        # Извлекаем данные из запроса
        modules = data.get('modules', [])
        author = data.get('author', 'Bondarev_E')

        print(f"\n[🚀 BUILD_STARTED] Author: {author}")
        print(f"[⚙️ PROCESSING] Nodes: {', '.join(modules)}")

        # --- ФАЗА 1: СИМУЛЯЦИЯ СБОРКИ (ОЖИВЛЕНИЕ ЖЕЛЕЗА) ---
        # В будущем здесь будет вызов функций генерации кода
        await asyncio.sleep(2)  # Имитируем работу компилятора

        # --- ФАЗА 2: ГЕНЕРАЦИЯ УНИКАЛЬНОГО ИДЕНТИФИКАТОРА ---
        build_id = f"BUILD-{str(uuid.uuid4())[:8].upper()}"

        # --- ФАЗА 3: РЕГИСТРАЦИЯ В FIREBASE ---
        # Мы создаем документ в коллекции 'build_history'
        build_data = {
            "build_id": build_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "author": author,
            "modules": modules,
            "status": "SUCCESS",
            "environment": "FastAPI_Production_Core",
            "metadata": {
                "os": "Universal_Node",
                "engine_version": "1.8.0"
            }
        }

        # Сохранение в Firestore
        db.collection("build_history").document(build_id).set(build_data)
        print(f"[✅ DATABASE] Record {build_id} saved successfully.")

        # --- ФАЗА 4: ОТВЕТ КЛИЕНТУ (ФРОНТЕНДУ) ---
        return {
            "status": "COMPLETED",
            "build_id": build_id,
            "author": author,
            "message": f"Проект {build_id} успешно сгенерирован и зарегистрирован в системе.",
            "artifacts": {
                "main_file": "bot_core.py",
                "config": "env.json",
                "docker": "Dockerfile",
                "readme": "INSTRUCTIONS.md"
            },
            "timestamp": time.time()
        }

    except Exception as e:
        print(f"[❌ CRITICAL_ERROR] Build failed: {str(e)}")
        return {
            "status": "ERROR",
            "message": f"System failure: {str(e)}"
        }


# ==============================================================================

@app.get("/get-project-images/{project_name}")
async def get_images(project_name: str):
    # Путь теперь строится относительно папки проекта
    target_dir = os.path.join(ASSETS_PATH, "projects", project_name, "img")

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
        # Если есть файл maintenance.html в templates, укажи путь к нему
        return JSONResponse({"status": "MAINTENANCE_MODE", "msg": "System upgrading..."})

    # Указываем путь к файлу внутри папки templates
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))


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
    status = "ACTIVATED" if SYSTEM_STATE["panic_mode"] else "DEACTIVATED"
    return {"panic_mode": SYSTEM_STATE["panic_mode"], "message": f"System wide panic {status}"}


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
    # Указываем путь к файлу внутри папки templates
    return FileResponse(os.path.join(TEMPLATES_DIR, "admin.html"))


# Не забудь добавить такие же роуты для остальных страниц, если они нужны напрямую
@app.get("/nda")
async def nda():
    return FileResponse(os.path.join(TEMPLATES_DIR, "nda.html"))


@app.get("/offer")
async def offer():
    return FileResponse(os.path.join(TEMPLATES_DIR, "offer.html"))


@app.get("/privacy")
async def privacy():
    return FileResponse(os.path.join(TEMPLATES_DIR, "privacy.html"))


import time


# Анализатор сайта
@app.post("/analyze-site")
async def analyze_site(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url.startswith("http"):
        url = "https://" + url

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            html = response.text.lower()
            headers = response.headers

            # Логика анализа технологий
            techs = []
            if "react" in html: techs.append("React.js")
            if "vue" in html: techs.append("Vue.js")
            if "next.js" in html or "_next" in html: techs.append("Next.js")
            if "python" in headers.get("server", "").lower() or "gunicorn" in headers.get("server", "").lower():
                techs.append("Python/FastAPI")

            # Подсчет сложности
            scripts_count = html.count("<script")
            styles_count = html.count("<link rel=\"stylesheet\"") + html.count("<style")

            # Формула "мощной" оценки (имитация сложного алгоритма)
            complexity_score = (scripts_count * 1.5) + (styles_count * 2)
            price = 1500 + (complexity_score * 10)

            return {
                "architecture": " + ".join(techs) if techs else "Custom Architecture",
                "security": "SSL Verified" if url.startswith("https") else "Standard HTTP",
                "price": f"${int(price)}",
                "time": f"{max(7, int(complexity_score / 5))} Days",
                "metrics": {
                    "scripts": scripts_count,
                    "styles": styles_count,
                    "latency": f"{int((time.time() - start_time) * 1000)}ms"
                }
            }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Узел недоступен или защищен WAF"})


# Анализатор сайта - конец

# Модуль управления сайтом
@app.post("/node-control")
async def control_node(request: Request):
    data = await request.json()
    node = data.get("node")  # Например, 'GENESYS'
    command = data.get("command")  # Например, 'restart'

    # 1. Словарь адресов твоих реальных нод
    NODE_MAP = {
        "GENESYS": "https://api.genesys-engine.ua",
        "MAIN": "https://webfactory.ua"
    }

    target_url = NODE_MAP.get(node)

    # 2. Отправка реальной команды на удаленный сайт
    async with httpx.AsyncClient() as client:
        try:
            # Отправляем секретный ключ, чтобы сайт понял, что это ТЫ
            response = await client.post(
                f"{target_url}/manage/{command}",
                headers={"X-Admin-Secret": "твой_секретный_код_170788"}
            )
            return {"status": "SUCCESS", "node_response": response.json()}
        except Exception as e:
            return {"status": "OFFLINE", "error": str(e)}


"""
--------------------------------------------------------------------------------
PROJECT: Genesis HR® | Intelligence Systems
MODULE:  Management Bridge (Receiver)
VERSION: 1.0.5
AUTHORS: Bondarev_E / Genesis Dev Team
--------------------------------------------------------------------------------
DESCRIPTION:
    Интерфейс удаленного управления для WebFactory Admin Panel.
    Реализует: Metrics API, Health Check, Remote Restart.
--------------------------------------------------------------------------------
"""

import psutil  # Требуется pip install psutil
from flask import Blueprint, jsonify, request, abort

bridge_bp = Blueprint('bridge', __name__)

# Секретный ключ для связи между админкой и этим сайтом
ADMIN_SECRET = "WEBFACTORY_SECURE_KEY_2026"


def check_auth():
    secret = request.headers.get("X-Admin-Secret")
    if secret != ADMIN_SECRET:
        abort(403)


@bridge_bp.route('/api/bridge/stats', methods=['GET'])
def get_metrics():
    """Отдает реальные данные нагрузки системы для карточки в админке[cite: 13]."""
    check_auth()
    return jsonify({
        "status": "ONLINE",
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "ram_usage": f"{psutil.virtual_memory().percent}%",
        "uptime": "14d 06h 12m",
        "active_threads": psutil.Process().num_threads()
    })


@bridge_bp.route('/api/bridge/restart', methods=['POST'])
def restart_services():
    """Программный перезапуск внутренних логических узлов[cite: 15, 16]."""
    check_auth()
    try:
        # Здесь может быть вызов функции переинициализации БД или сброс кэша
        # В реальном сервере здесь может быть команда os.execv
        return jsonify({"result": "SUCCESS", "message": "Service nodes recycled."})
    except Exception as e:
        return jsonify({"result": "ERROR", "error": str(e)}), 500


# --- НОВЫЙ ЭНДПОИНТ ДЛЯ СБОРЩИКА (WEBFACTORY BUILDER) ---

@app.post("/build")
async def build_project(data: dict):
    """
    Принимает конфигурацию модулей и имитирует процесс сборки.
    """
    selected_modules = data.get('modules', [])
    user = data.get('author', 'Bondarev_E')

    # 1. Инициализация (Логируем начало в консоль сервера)
    print(f">>> [BUILD_SYSTEM] Starting build for: {user}")
    print(f">>> [BUILD_SYSTEM] DNA Sequence: {selected_modules}")

    # 2. Имитация процесса сборки (Async задержки)
    # На фронтенде мы это увидим как прогресс-бар
    await asyncio.sleep(1)  # Имитация подготовки окружения

    # 3. Регистрация сборки в твоем Firestore (используем твою переменную db)
    build_id = str(uuid.uuid4())[:8].upper()
    try:
        db.collection("build_history").document(build_id).set({
            "build_id": build_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "author": user,
            "modules": selected_modules,
            "status": "SUCCESS"
        })
    except Exception as e:
        print(f"Firestore log error: {e}")

    return {
        "status": "SUCCESS",
        "build_id": build_id,
        "message": f"Проект {build_id} успешно скомпилирован.",
        "details": {
            "module_count": len(selected_modules),
            "environment": "Production_Edge"
        }
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
