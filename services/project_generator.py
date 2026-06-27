# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /backend/services/project_generator.py
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Генератор структуры проекта и Docker-конфигураций.
# PURPOSE: Создание архива с кодом, зависимостями и инструкциями по запуску.
# DEPENDENCIES: zipfile, jinja2
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

import zipfile
import io


class ProjectGenerator:
    def __init__(self, bot_code: str, selected_modules: list):
        self.bot_code = bot_code
        self.modules = selected_modules

    def create_deployment_package(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            # 1. Основной код бота
            zf.writestr('main.py', self.bot_code)

            # 2. Файл зависимостей
            requirements = "aiogram==3.4.1\npython-dotenv==1.0.0\n"
            if "rag" in self.modules: requirements += "langchain\nchromadb\n"
            zf.writestr('requirements.txt', requirements)

            # 3. Dockerfile для мгновенного запуска
            dockerfile = """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
            """
            zf.writestr('Dockerfile', dockerfile)

            # 4. README с инструкцией
            readme = (f"# Ваша нейросетевая империя готова\nПросто добавьте TOKEN в .env и запустите `docker build -t "
                      f"my_bot .`")
            zf.writestr('README.md', readme)

        return buffer.getvalue()