FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn

# Копируем код
COPY . .

# ЗАПУСК ЧЕРЕЗ GUNICORN (Это стандарт для Google Cloud Run)
CMD ["gunicorn", "main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]