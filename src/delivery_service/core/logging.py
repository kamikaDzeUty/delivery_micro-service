import asyncio
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from src.delivery_service.core.config import settings


def setup_logging() -> None:
    """
    Настройка системы логирования для всего приложения.
    """
    # Создаем директорию для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Конфигурация логирования
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "celery": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/celery.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "src.delivery_service": {
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "src.delivery_service.api": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "src.delivery_service.services": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "src.delivery_service.repositories": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "src.delivery_service.tasks": {
                "level": "INFO",
                "handlers": ["console", "celery"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "celery"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "aiohttp": {
                "level": "WARNING",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
        },
    }

    # Применяем конфигурацию
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с указанным именем.
    
    Args:
        name: Имя логгера (обычно __name__)
        
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


# Middleware для логирования HTTP запросов
class RequestLoggingMiddleware:
    """
    Middleware для логирования HTTP запросов и ответов.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("src.delivery_service.api.requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Логируем входящий запрос
            method = scope["method"]
            path = scope["path"]
            self.logger.info(f"Запрос: {method} {path}")
            
            # Создаем кастомный send для логирования ответа
            async def custom_send(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    self.logger.info(f"Ответ: {method} {path} - {status_code}")
                await send(message)
            
            await self.app(scope, receive, custom_send)
        else:
            await self.app(scope, receive, send)


# Декоратор для логирования функций
def log_function_call(logger_name: Optional[str] = None):
    """
    Декоратор для логирования вызовов функций.
    
    Args:
        logger_name: Имя логгера (если не указано, используется имя модуля)
    """
    def decorator(func):
        logger = get_logger(logger_name or f"{func.__module__}.{func.__qualname__}")
        
        async def async_wrapper(*args, **kwargs):
            logger.debug(f"Вызов {func.__name__} с аргументами args={args}, kwargs={kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} успешно завершен")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} завершился с ошибкой: {e}")
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger.debug(f"Вызов {func.__name__} с аргументами args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} успешно завершен")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} завершился с ошибкой: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 