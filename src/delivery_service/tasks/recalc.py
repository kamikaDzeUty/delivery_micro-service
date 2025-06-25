# src/delivery_service/tasks/recalc.py
from uuid import UUID
from asgiref.sync import async_to_sync

from src.delivery_service.core.celery_app import celery_app
from src.delivery_service.core.database import async_session
from src.delivery_service.repositories.package_repository import PackageRepository

@celery_app.task(name="delivery_service.recalc_shipping_cost")
def recalc_shipping_cost(package_id: str) -> None:
    from src.delivery_service.services.package_service import PackageService
    """
    Celery-таск: берёт UUID, инициализирует async-сессию и
    вызывает сервисный метод update_shipping_cost.
    """
    async def _inner(pkg_id: str):
        async with async_session() as session:
            repo = PackageRepository(session)
            service = PackageService(repo)
            await service.update_shipping_cost(UUID(pkg_id))

    async_to_sync(_inner)(package_id)
