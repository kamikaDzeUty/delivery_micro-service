# src/delivery_service/tasks/recalc.py
import asyncio
import logging
from uuid import UUID
from typing import List

from celery import current_task
from src.delivery_service.core.celery_app import celery_app
from src.delivery_service.core.database import async_session
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.services.rate_service import RateService
from src.delivery_service.services.shipping_service import ShippingService
from src.delivery_service.services.package_service import PackageService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="delivery_service.recalc_shipping_cost",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    bind=True,
)
def recalc_shipping_cost(self, package_id: str) -> dict:
    """
    Пересчитывает стоимость доставки для посылки.
    Использует синхронный подход для Celery.
    """
    try:
        pkg_uuid = UUID(package_id)
        logger.info(f"Starting shipping cost recalculation for package {pkg_uuid}")
        
        # Запускаем асинхронную функцию в синхронном контексте
        result = asyncio.run(_recalc_shipping_cost_async(pkg_uuid))
        
        if result is None:
            logger.warning(f"Package {pkg_uuid} not found")
            return {"status": "not_found", "package_id": package_id}
        
        logger.info(f"Successfully recalculated shipping cost for package {pkg_uuid}: {result.shipping_cost}")
        return {
            "status": "success", 
            "package_id": package_id,
            "shipping_cost": str(result.shipping_cost) if result.shipping_cost else None
        }
        
    except ValueError as e:
        logger.error(f"Invalid package ID format: {package_id}")
        raise self.retry(countdown=60, max_retries=2)
    except Exception as e:
        logger.error(f"Error recalculating shipping cost for package {package_id}: {e}")
        raise self.retry(countdown=120, max_retries=3)


@celery_app.task(
    name="delivery_service.bulk_recalc_shipping_cost",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
    bind=True,
)
def bulk_recalc_shipping_cost(self, package_ids: List[str]) -> dict:
    """
    Пересчитывает стоимость доставки для нескольких посылок.
    """
    logger.info(f"Starting bulk recalculation for {len(package_ids)} packages")
    
    results = {
        "total": len(package_ids),
        "successful": 0,
        "failed": 0,
        "not_found": 0,
        "errors": []
    }
    
    for package_id in package_ids:
        try:
            # Используем существующую задачу для каждой посылки
            task_result = recalc_shipping_cost.delay(package_id)
            result = task_result.get(timeout=30)  # Ждем результат 30 секунд
            
            if result["status"] == "success":
                results["successful"] += 1
            elif result["status"] == "not_found":
                results["not_found"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Package {package_id}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error processing package {package_id}: {e}")
            results["failed"] += 1
            results["errors"].append(f"Package {package_id}: {str(e)}")
    
    logger.info(f"Bulk recalculation completed: {results}")
    return results


async def _recalc_shipping_cost_async(pkg_uuid: UUID):
    """
    Асинхронная функция для пересчета стоимости доставки.
    """
    async with async_session() as session:
        # Создаем все необходимые зависимости
        repo = PackageRepository(session)
        
        # Для Celery задач создаем простые сервисы без внешних зависимостей
        # В реальном проекте можно использовать DI контейнер
        from src.delivery_service.core.config import settings
        import aiohttp
        from redis.asyncio import Redis
        
        # Создаем HTTP клиент
        timeout = aiohttp.ClientTimeout(total=settings.http_timeout)
        async with aiohttp.ClientSession(timeout=timeout) as http_client:
            # Создаем Redis клиент
            redis_client = Redis.from_url(str(settings.redis_url))
            try:
                # Создаем сервисы
                rate_service = RateService(http_client, redis_client)
                shipping_service = ShippingService(rate_service)
                package_service = PackageService(repo, shipping_service)
                
                # Выполняем пересчет
                return await package_service.update_shipping_cost(pkg_uuid)
            finally:
                await redis_client.close()
