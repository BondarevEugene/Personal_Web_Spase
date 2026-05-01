# Используем легковесный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости (создай файл requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код и файлы фронтенда
COPY . .

# Запускаем FastAPI через uvicorn
CMD ["uvicorn", "main_8:app", "--host", "0.0.0.0", "--port", "8080"]