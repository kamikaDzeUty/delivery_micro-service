# Delivery Microservice

Микросервис для регистрации посылок и расчёта стоимости доставки с автоматическим расчетом через Celery.

## Описание

Сервис предоставляет REST API для:
- Управления типами посылок
- Регистрации посылок с автоматическим расчетом стоимости
- Расчета стоимости доставки с учетом курса валют
- Асинхронного пересчета стоимости через Celery
- Мониторинга Celery задач

## Архитектура

- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0** - ORM с асинхронной поддержкой
- **PostgreSQL** - основная база данных
- **Redis** - кеширование курсов валют и результаты Celery
- **RabbitMQ** - очередь сообщений для Celery
- **Celery** - асинхронные задачи с автоматическим расчетом
- **Docker & Docker Compose** - контейнеризация

## Структура проекта

```
src/delivery_service/
├── api/                    # FastAPI роутеры
├── core/                   # Конфигурация и зависимости
├── models/                 # SQLAlchemy модели
├── repositories/           # Слой доступа к данным
├── schemas/                # Pydantic схемы
├── services/               # Бизнес-логика
└── tasks/                  # Celery задачи
```

## Установка и запуск

### Требования

- Docker & Docker Compose
- Python 3.12+

### Переменные окружения

Создайте файл `.env` в корне проекта со следующим содержимым:

```bash
# Database Configuration
POSTGRES_USER=delivery_user
POSTGRES_PASSWORD=delivery_pass
POSTGRES_DB=delivery_db
DATABASE_URL=postgresql+asyncpg://delivery_user:delivery_pass@db:5432/delivery_db

# Redis Configuration
REDIS_PASSWORD=redis_pass
REDIS_URL=redis://:redis_pass@redis:6379/0

# RabbitMQ Configuration
RABBITMQ_USER=delivery_user
RABBITMQ_PASSWORD=delivery_pass
CELERY_BROKER_URL=amqp://delivery_user:delivery_pass@rabbitmq:5672/

# External APIs
CBR_API_URL=https://www.cbr-xml-daily.ru/daily_json.js

# Business Logic Coefficients
WEIGHT_COEFFICIENT=1.0
VALUE_COEFFICIENT=0.1
RATE_TTL_SECONDS=3600

# HTTP Client Settings
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3

# Celery Configuration
CELERY_RESULT_BACKEND=redis://:redis_pass@redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=Europe/Moscow
CELERY_ENABLE_UTC=true
CELERY_TASK_ACKS_LATE=true
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_WORKER_CONCURRENCY=4
```

**Важно:** Файл `.env` уже добавлен в `.gitignore` для безопасности.

### Запуск с Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f app

# Остановка
docker-compose down
```

### Локальная разработка

```bash
# Установка зависимостей
poetry install

# Запуск базы данных и Redis
docker-compose up -d db redis rabbitmq

# Применение миграций
alembic upgrade head

# Запуск приложения
uvicorn src.delivery_service.main:app --reload

# Запуск Celery worker
celery -A src.delivery_service.core.celery_app.celery_app worker --loglevel=info
```

## API Endpoints

### Типы посылок

- `GET /package-types/` - список всех типов
- `POST /package-types/` - создание нового типа

### Посылки

- `GET /packages/` - список посылок с фильтрацией и пагинацией
- `POST /packages/` - создание новой посылки (автоматически запускает расчет стоимости)
- `GET /packages/{id}` - получение посылки по ID
- `POST /packages/{id}/calculate` - расчет стоимости доставки (синхронно)
- `POST /packages/recalculate-pending` - массовый пересчет всех посылок без стоимости

### Мониторинг Celery

- `GET /monitoring/celery/stats` - статистика воркеров и задач
- `GET /monitoring/celery/task/{task_id}` - статус конкретной задачи
- `POST /monitoring/celery/task/{task_id}/revoke` - отмена задачи

### Health Check

- `GET /health` - проверка состояния сервиса

## Celery задачи

### Автоматические задачи

- `recalc_shipping_cost` - автоматически запускается при создании посылки
- `bulk_recalc_shipping_cost` - массовый пересчет для нескольких посылок

### Особенности

- **Автоматический запуск**: При создании посылки автоматически отправляется задача на расчет
- **Retry логика**: Автоматические повторы при ошибках с exponential backoff
- **Мониторинг**: Полная статистика выполнения задач
- **Отмена задач**: Возможность отменить выполняющиеся задачи

## Рабочий процесс

1. **Создание посылки**: `POST /packages/`
   - Посылка сохраняется в БД без стоимости
   - Автоматически отправляется задача в Celery
   - Через 5 секунд начинается расчет стоимости

2. **Расчет стоимости**: Celery worker
   - Получает курс валют из кеша или API ЦБ
   - Рассчитывает стоимость по формуле
   - Обновляет посылку в БД

3. **Мониторинг**: `GET /monitoring/celery/stats`
   - Просмотр активных задач
   - Статистика выполнения
   - Отмена проблемных задач

## Разработка


### Миграции базы данных

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```


## Логирование

Сервис использует стандартное Python logging с настройками для:
- HTTP запросов
- Операций с базой данных
- Celery задач
- Внешних API вызовов