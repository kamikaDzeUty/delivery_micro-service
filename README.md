# Delivery Microservice

Микросервис для регистрации посылок и расчёта стоимости доставки с автоматическим расчетом через Celery.

## Описание

Сервис предоставляет REST API для:
- Управления типами посылок
- Регистрации посылок с автоматическим расчетом стоимости
- Расчета стоимости доставки с учетом курса валют
- Асинхронного пересчета стоимости через Celery
- Мониторинга Celery задач
- Валидации данных и логирования

## Архитектура

- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0** - ORM с асинхронной поддержкой
- **PostgreSQL** - основная база данных
- **Redis** - кеширование курсов валют и результаты Celery
- **RabbitMQ** - очередь сообщений для Celery
- **Celery** - асинхронные задачи с автоматическим расчетом
- **Docker & Docker Compose** - контейнеризация
- **Pydantic v2** - валидация данных и сериализация
- **Logging** - структурированное логирование

## Структура проекта

```
src/delivery_service/
├── api/                    # FastAPI роутеры
├── core/                   # Конфигурация и зависимости
│   ├── logging.py         # Система логирования
│   └── config.py          # Конфигурация приложения
├── models/                 # SQLAlchemy модели
├── repositories/           # Слой доступа к данным
├── schemas/                # Pydantic v2 схемы с валидацией
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

## Валидация данных

### Pydantic v2 Схемы

Все входные данные валидируются с помощью современных Pydantic v2 схем:

#### PackageCreate
```python
{
    "name": "Электроника",           # 1-100 символов, не пустое
    "weight": "2.5",                 # 0-1000 кг
    "declared_value": "500.00",      # 0-1,000,000 USD
    "type_id": "uuid-here"           # Валидный UUID
}
```

#### PackageTypeCreate
```python
{
    "name": "Хрупкие предметы"       # 1-50 символов, не пустое
}
```

### Валидация полей

#### Field валидаторы
- **Название посылки**: `min_length=1, max_length=100`
- **Вес**: `gt=0, le=1000` (больше 0, меньше или равно 1000 кг)
- **Объявленная стоимость**: `ge=0, le=1000000` (от 0 до 1,000,000 USD)
- **ID типа**: валидный UUID
- **Название типа**: `min_length=1, max_length=50`

#### Кастомные валидаторы
```python
@field_validator('name')
@classmethod
def validate_name(cls, v: str) -> str:
    """Валидация названия посылки"""
    if not v or not v.strip():
        raise ValueError('Название посылки не может быть пустым')
    return v.strip()
```

### Особенности Pydantic v2

- **@field_validator** вместо устаревшего @validator
- **@classmethod** декоратор обязателен
- **Типизация** параметров и возвращаемых значений
- **Field** валидаторы для базовых ограничений
- **Кастомные валидаторы** для сложной бизнес-логики

## Логирование

### Структура логов

Система логирования настроена с разделением по уровням и типам:

```
logs/
├── app.log          # Основные логи приложения (INFO+)
├── error.log        # Только ошибки (ERROR+)
└── celery.log       # Логи Celery задач
```

### Уровни логирования

- **DEBUG**: Детальная отладочная информация
- **INFO**: Основные операции (создание, получение, расчет)
- **WARNING**: Предупреждения (не найдено, fallback значения)
- **ERROR**: Ошибки (API недоступен, валидация не прошла)

### Форматы логов

- **Console**: Краткий формат для разработки
- **File**: Детальный формат с временными метками и контекстом
- **JSON**: Структурированный формат для анализа

### Примеры логов

```bash
# Создание посылки
2024-01-15 10:30:15 - src.delivery_service.api.packages - INFO - Creating package: Электроника (weight: 2.5kg, value: $500.00)
2024-01-15 10:30:15 - src.delivery_service.services.package_service - INFO - Package created successfully: 123e4567-e89b-12d3-a456-426614174000

# Расчет стоимости
2024-01-15 10:30:20 - src.delivery_service.tasks.recalc - INFO - Starting shipping cost recalculation for package 123e4567-e89b-12d3-a456-426614174000
2024-01-15 10:30:21 - src.delivery_service.services.rate_service - INFO - Received rate from CBR: 95.45
2024-01-15 10:30:21 - src.delivery_service.services.package_service - INFO - Calculated shipping cost for package 123e4567-e89b-12d3-a456-426614174000: 7500.50
```

### Мониторинг логов

```bash
# Просмотр логов в реальном времени
tail -f logs/app.log

# Поиск ошибок
grep "ERROR" logs/error.log

# Анализ производительности
grep "shipping cost" logs/app.log | awk '{print $1, $2, $NF}'
```

## Celery задачи

### Автоматические задачи

- `recalc_shipping_cost` - автоматически запускается при создании посылки
- `bulk_recalc_shipping_cost` - массовый пересчет для нескольких посылок

### Особенности

- **Автоматический запуск**: При создании посылки автоматически отправляется задача на расчет
- **Retry логика**: Автоматические повторы при ошибках с exponential backoff
- **Мониторинг**: Полная статистика выполнения задач
- **Отмена задач**: Возможность отменить выполняющиеся задачи
- **Логирование**: Детальные логи выполнения задач

## Рабочий процесс

1. **Создание посылки**: `POST /packages/`
   - Валидация входных данных через Pydantic v2
   - Посылка сохраняется в БД без стоимости
   - Автоматически отправляется задача в Celery
   - Через 5 секунд начинается расчет стоимости

2. **Расчет стоимости**: Celery worker
   - Получает курс валют из кеша или API ЦБ
   - Рассчитывает стоимость по формуле
   - Обновляет посылку в БД
   - Логирует все этапы процесса

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

### Добавление новых валидаций

1. Обновите схему в `schemas/` используя Pydantic v2 синтаксис
2. Добавьте `@field_validator` с `@classmethod`
3. Используйте `Field` для базовых ограничений
4. Обновите тесты
5. Проверьте документацию API

### Настройка логирования

1. Измените конфигурацию в `core/logging.py`
2. Добавьте новые логгеры при необходимости
3. Настройте ротацию файлов

### Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск тестов валидации
pytest tests/test_validation.py -v

# Запуск с покрытием
pytest --cov=src/delivery_service
```

## Безопасность

- CORS настроен для конкретных доменов
- Валидация всех входных данных через Pydantic v2
- Логирование всех операций
- Обработка ошибок без утечки информации
- Типизация всех валидаторов