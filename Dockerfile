# Stage 1: сборка зависимостей
FROM python:3.12-slim AS builder

WORKDIR /app

# Устанавливаем компиляторы и libpq-dev для asyncpg
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Ставим Poetry без создания venv
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.8.1" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

RUN curl -sSL https://install.python-poetry.org | python3 - \
 && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry

# Копируем только манифесты и ставим prod-зависимости
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-ansi

# Stage 2: финальный образ
FROM python:3.12-slim

WORKDIR /app

# Нужен libpq для runtime asyncpg
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Копируем зависимости (site-packages) и скрипты (alembic, uvicorn и др.)
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY . .

# Чтобы Python видел модуль delivery_service в src/
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# При старте: миграции + запуск FastAPI
CMD ["sh", "-c", "alembic upgrade head && uvicorn delivery_service.main:app --host 0.0.0.0 --port 8080"]
