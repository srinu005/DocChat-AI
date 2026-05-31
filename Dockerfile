# ── Build stage ─────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ── App stage ────────────────────────────────────────────────────
FROM base AS app

COPY app/       ./app/
COPY frontend/  ./frontend/
COPY .env.example .env

RUN mkdir -p /tmp/docai_uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Worker stage ─────────────────────────────────────────────────
FROM base AS worker

COPY app/ ./app/
COPY .env.example .env

CMD ["celery", "-A", "app.core.celery_app.celery_app", "worker", \
     "--loglevel=info", "--concurrency=4"]
