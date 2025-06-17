# src/delivery_service/core/config.py
from pydantic import PostgresDsn, RedisDsn, HttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: PostgresDsn
    redis_url: RedisDsn
    cbr_api_url: HttpUrl
    rate_ttl_seconds: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Ошибка при валидации конфигурации: {e}")
