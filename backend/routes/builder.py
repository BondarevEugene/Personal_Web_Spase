import io
import os
import sys
import shutil
import zipfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List
import docker

# Импортируем твои существующие сервисы генерации из структуры проекта
from services.bot_factory import BotFactory, MODULES_REGISTRY
from backend.services.project_generator import ProjectGenerator

router = APIRouter(prefix="/api/builder", tags=["OmniFactory Bot Builder Core"])

# Инициализируем клиент Docker. На Windows он автоматически свяжется с Docker Desktop
try:
    docker_client = docker.from_env()
except Exception as ex:
    print(f"🚨 [DOCKER CRITICAL] Не удалось подключиться к Docker Engine: {str(ex)}")
    docker_client = None

# Директория для временной сборки Docker-образов перед запуском
BUILD_ROOT_DIR = os.path.join(os.getcwd(), "docker_builds")
os.makedirs(BUILD_ROOT_DIR, exist_ok=True)


class BotBuildRequest(BaseModel):
    selected_ids: List[str]
    bot_token: str
    user_id: str = "bondarev_e"


class BotControlRequest(BaseModel):
    bot_token: str


# =============================================================================
# ДИНАМИЧЕСКИЙ РЕЕСТР: ОТДАЕМ СПИСОК МОДУЛЕЙ НА ФРОНТЕНД
# =============================================================================
@router.get("/modules")
async def get_available_modules():
    """
    Эндпоинт OmniFactory EVO: считывает метаданные из MODULES_REGISTRY
    и передает их фронтенду для динамического построения интерфейса кубиков.
    """
    try:
        modules_list = []
        for mid, info in MODULES_REGISTRY.items():
            modules_list.append({
                "id": mid,
                "label": info.get("label", mid),
                "cat": info.get("cat", "common"),
                "desc": info.get("desc", "")
            })
        return {"modules": modules_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга кодовой матрицы ядра: {str(e)}")


# =============================================================================
# РЕЖИМ 1: СКАЧАТЬ ZIP-АРХИВ ИСХОДНИКОВ
# =============================================================================
@router.post("/generate")
async def generate_bot_package(request: BotBuildRequest):
    if not request.selected_ids:
        raise HTTPException(status_code=400, detail="Модули для сборки не выбраны.")

    try:
        factory = BotFactory(selected_ids=request.selected_ids)
        bot_raw_code = factory.generate()
        bot_raw_code = bot_raw_code.replace("YOUR_TOKEN", request.bot_token.strip())

        generator = ProjectGenerator(bot_code=bot_raw_code, selected_modules=request.selected_ids)
        zip_buffer = generator.create_deployment_package()
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=compiled_bot_project.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Критический сбой генерации архива: {str(e)}")


# =============================================================================
# РЕЖИМ 2: ПРОМЫШЛЕННЫЙ SaaS (УПРАВЛЕНИЕ DOCKER-КОНТЕЙНЕРАМИ)
# =============================================================================
@router.post("/start")
async def start_bot_process(request: BotBuildRequest):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Служба Docker на сервере Windows не запущена.")

    token = request.bot_token.strip()
    if not request.selected_ids:
        raise HTTPException(status_code=400, detail="Архитектурные модули не выбраны.")

    # Формируем безопасные имена для Docker (без двоеточий, в нижнем регистре)
    safe_token = token.replace(":", "_").lower()
    container_name = f"omnifactory_bot_{safe_token}"
    image_name = f"omnifactory_img_{safe_token}"

    try:
        # Проверяем, запущен ли уже такой бот в Docker
        try:
            container = docker_client.containers.get(container_name)
            if container.status == "running":
                return {"status": "already_running",
                        "detail": "Этот бот уже развернут и работает внутри изолированного контейнера."}
            else:
                # Если контейнер существует, но остановлен — удаляем старый хвост
                container.remove(force=True)
        except docker.errors.NotFound:
            pass

        # 1. Сборка кода через Фабрику
        factory = BotFactory(selected_ids=request.selected_ids)
        bot_raw_code = factory.generate().replace("YOUR_TOKEN", token)

        # 2. Упаковка во временный zip-буфер
        generator = ProjectGenerator(bot_code=bot_raw_code, selected_modules=request.selected_ids)
        zip_buffer = generator.create_deployment_package()
        zip_buffer.seek(0)

        # 3. Разворачиваем временную рабочую директорию на диске для сборки Docker-образа
        build_workspace = os.path.join(BUILD_ROOT_DIR, container_name)
        os.makedirs(build_workspace, exist_ok=True)

        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extractall(build_workspace)

        # 4. Собираем изолированный Docker-образ "на лету"
        print(f"📦 [DOCKER BUILD] Создание образа {image_name}...")
        image, build_logs = docker_client.images.build(
            path=build_workspace,
            tag=image_name,
            rm=True
        )

        # Удаляем временные исходники с хост-машины Windows, они уже внутри образа
        shutil.rmtree(build_workspace, ignore_errors=True)

        # 5. Запуск контейнера со строгими промышленными лимитами ресурсов
        print(f"🚀 [DOCKER RUN] Запуск контейнера {container_name}...")
        container = docker_client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,  # Фоновый режим демона
            restart_policy={"Name": "unless-stopped"},  # Автоподнятие бота при рестарте Windows/Docker
            mem_limit="50m",  # Жесткое ограничение памяти: 50 Мегабайт на бота
            nano_cpus=100000000,  # Ограничение CPU: максимум 10% от мощности одного ядра процессора
            stdout=True,
            stderr=True
        )

        return {
            "status": "success",
            "container_id": container.short_id,
            "container_name": container_name,
            "detail": f"Бот успешно запущен в Docker-контейнере [{container.short_id}]."
        }

    except Exception as e:
        if 'build_workspace' in locals() and os.path.exists(build_workspace):
            shutil.rmtree(build_workspace, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Ошибка Docker-конвейера: {str(e)}")


@router.post("/stop")
async def stop_bot_process(request: BotControlRequest):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Служба Docker недоступна.")

    token = request.bot_token.strip()
    safe_token = token.replace(":", "_").lower()
    container_name = f"omnifactory_bot_{safe_token}"
    image_name = f"omnifactory_img_{safe_token}"

    try:
        container = docker_client.containers.get(container_name)
        print(f"🛑 [DOCKER STOP] Уничтожение контейнера {container_name}...")

        # Принудительно останавливаем и удаляем контейнер
        container.remove(force=True)

        # Чистим скомпилированный под него образ, чтобы не забивать диск на Windows
        try:
            docker_client.images.remove(image=image_name, force=True)
        except Exception:
            pass

        return {"status": "stopped", "detail": "Контейнер бота успешно уничтожен. Ресурсы хоста свободны."}

    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Активный контейнер Docker для этого бота не найден.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при остановке контейнера: {str(e)}")


# =============================================================================
# ШЛЮЗ ТЕЛЕМЕТРИИ: ВЫТЯГИВАЕМ ЛОГИ ИЗНУТРИ КОНТЕЙНЕРА
# =============================================================================
@router.get("/logs/{bot_token}")
async def get_bot_container_logs(bot_token: str, tail_lines: int = 40):
    """
    Считывает живые логи (stdout/stderr) прямо из изолированной среды Docker.
    """
    if not docker_client:
        return {"logs": "[DOCKER_OFFLINE] Нет связи с Docker Engine."}

    container_name = f"omnifactory_bot_{bot_token.strip().replace(':', '_').lower()}"
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=tail_lines, stdout=True, stderr=True).decode("utf-8")
        return {"logs": logs}
    except docker.errors.NotFound:
        return {"logs": "[OFFLINE] Контейнер бота сейчас не запущен."}
    except Exception as e:
        return {"logs": f"[ERROR] Не удалось извлечь телеметрию: {str(e)}"}