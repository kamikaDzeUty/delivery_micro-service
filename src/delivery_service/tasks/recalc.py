# src/delivery_service/tasks/recalc.py
import asyncio
from uuid import UUID

from src.delivery_service.core.celery_app import celery_app
from src.delivery_service.core.database import async_session
from src.delivery_service.repositories.package_repository import PackageRepository


@celery_app.task(
    name="delivery_service.recalc_shipping_cost",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def recalc_shipping_cost(package_id: str) -> None:
    """
    Celery-таск под pre-fork пул (production-ready).
    На каждый вызов создаётся свой event-loop через asyncio.run().
    """
    from src.delivery_service.services.package_service import PackageService
    async def _inner(pkg_uuid: UUID):
        async with async_session() as session:
            repo = PackageRepository(session)
            service = PackageService(repo)
            await service.update_shipping_cost(pkg_uuid)

    pkg_uuid = UUID(package_id)
    asyncio.run(_inner(pkg_uuid))
