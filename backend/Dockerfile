FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

COPY backend /app/backend

EXPOSE 8080

CMD ["sh", "-c", "python -m backend.scripts.run_migrations && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
