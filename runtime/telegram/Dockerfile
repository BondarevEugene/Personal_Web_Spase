FROM python:3.12.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 OMNI_RUNTIME_BOOT=1
WORKDIR /app
RUN useradd --uid 10001 --create-home omni
COPY runtime/telegram/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
COPY runtime/telegram/app.py /app/app.py
COPY runtime/telegram/scenario.py /app/scenario.py
COPY runtime/telegram/state.py /app/state.py
COPY runtime/telegram/postgres_state.py /app/postgres_state.py
COPY runtime/telegram/postgres_webhook.py /app/postgres_webhook.py
COPY runtime/telegram/outbox.py /app/outbox.py
COPY runtime/telegram/maintenance.py /app/maintenance.py
COPY runtime/telegram/backup.py /app/backup.py
RUN mkdir -p /data && chown 10001:10001 /data
USER 10001
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --no-proxy-headers"]
