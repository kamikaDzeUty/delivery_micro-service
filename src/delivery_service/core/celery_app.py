# src/delivery_service/core/celery_app.py
from celery import Celery
from src.delivery_service.core.config import settings

celery_app = Celery(
    "delivery_service",
    broker=settings.rabbitmq_url,
    backend=None,
    include=[
        "src.delivery_service.tasks.recalc",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)
