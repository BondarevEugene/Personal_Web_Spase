# Используем легковесный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта (включая assets и index.html)
COPY . .

# Открываем порт 8080 (стандарт для Cloud Run)
EXPOSE 8080

# Запускаем сервер, указывая порт из переменной окружения
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]