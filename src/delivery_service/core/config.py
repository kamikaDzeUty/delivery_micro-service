from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # Redis
    redis_url: str

    # External APIs
    cbr_api_url: str = "https://www.cbr-xml-daily.ru/daily_json.js"

    # Business logic coefficients
    weight_coefficient: float = 1.0
    value_coefficient: float = 0.1
    rate_ttl_seconds: int = 3600  # 1 hour

    # Message queue
    rabbitmq_url: str

    # HTTP client settings
    http_timeout: int = 30
    http_max_retries: int = 3

    # Celery settings
    celery_broker_url: str
    celery_result_backend: str | None = None
    celery_task_serializer: str = "json"
    celery_accept_content: list[str] = ["json"]
    celery_result_serializer: str = "json"
    celery_timezone: str = "Europe/Moscow"
    celery_enable_utc: bool = True
    celery_task_acks_late: bool = True
    celery_worker_prefetch_multiplier: int = 1
    celery_worker_max_tasks_per_child: int = 1000
    celery_worker_concurrency: int = 4

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Ошибка при валидации конфигурации: {e}")
