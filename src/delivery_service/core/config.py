# src/delivery_service/core/config.py
from pydantic import  RedisDsn, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    redis_url: RedisDsn
    cbr_api_url: str
    rate_ttl_seconds: int
    rabbitmq_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Ошибка при валидации конфигурации: {e}")
