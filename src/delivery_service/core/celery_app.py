from celery import Celery
from src.delivery_service.core.config import settings

celery_app = Celery(
    "delivery_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.delivery_service.tasks.recalc",
    ],
)

# Основные настройки
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    accept_content=settings.celery_accept_content,
    result_serializer=settings.celery_result_serializer,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_acks_late=settings.celery_task_acks_late,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    worker_concurrency=settings.celery_worker_concurrency,
)

# Дополнительные настройки
celery_app.conf.update(
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
    event_queue_expires=60.0,
    worker_state_db=None,
    result_expires=3600,
    task_soft_time_limit=300,
    task_time_limit=600,
)

# Настройки для мониторинга
celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
)
