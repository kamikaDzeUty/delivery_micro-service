from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from src.delivery_service.models.package import Package
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.services.shipping_service import ShippingService
from src.delivery_service.schemas.package import PackageCreate
from src.delivery_service.core.celery_app import celery_app
from src.delivery_service.core.logging import get_logger

logger = get_logger(__name__)

class PackageService:
    """
    Сервисный слой для работы с посылками:
    – создание,
    – получение списка,
    – пересчёт стоимости доставки.
    """

    def __init__(
        self,
        repo: PackageRepository,
        shipping: ShippingService,
    ):
        self._repo = repo
        self._shipping = shipping

    async def create_package(self, payload: PackageCreate) -> Package:
        """
        Создает новую посылку из Pydantic схемы и запускает автоматический расчет стоимости.
        """
        logger.info(f"Creating new package: {payload.name}")
        
        # Конвертируем Pydantic схему в ORM модель
        pkg = Package(**payload.model_dump())
        created_pkg = await self._repo.create(pkg)
        
        logger.info(f"Package created successfully with ID: {created_pkg.id}")
        
        # Запускаем асинхронный расчет стоимости через Celery
        self._schedule_shipping_calculation(created_pkg.id)
        
        return created_pkg

    def _schedule_shipping_calculation(self, package_id: UUID) -> None:
        """
        Отправляет задачу на расчет стоимости доставки в Celery.
        """
        try:
            # Отправляем задачу в очередь
            task = celery_app.send_task(
                'delivery_service.recalc_shipping_cost',
                args=[str(package_id)],
                countdown=5,  # Задержка 5 секунд перед выполнением
            )
            logger.info(f"Task scheduled for package {package_id}: {task.id}")
        except Exception as e:
            logger.error(f"Failed to schedule task for package {package_id}: {e}")

    async def get_package(self, pkg_id: UUID) -> Optional[Package]:
        logger.debug(f"Getting package with ID: {pkg_id}")
        return await self._repo.get(pkg_id)

    async def list_packages(
        self,
        *,
        type_id: Optional[UUID] = None,
        has_cost: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, Sequence[Package]]:
        logger.debug(f"Listing packages: type_id={type_id}, has_cost={has_cost}, limit={limit}, offset={offset}")
        return await self._repo.list(
            type_id=type_id,
            has_cost=has_cost,
            limit=limit,
            offset=offset,
        )

    async def update_shipping_cost(self, pkg_id: UUID) -> Optional[Package]:
        """
        Пересчитывает и сохраняет shipping_cost у посылки.
        Возвращает обновленную посылку или None, если посылки нет.
        """
        logger.info(f"Updating shipping cost for package: {pkg_id}")
        
        pkg = await self._repo.get(pkg_id)
        if pkg is None:
            logger.warning(f"Package not found: {pkg_id}")
            return None

        cost = await self._shipping.calculate_shipping_cost(
            weight_kg=pkg.weight,
            declared_value_usd=pkg.declared_value,
        )
        
        logger.info(f"Calculated shipping cost for package {pkg_id}: {cost}")
        
        # Сохраняем обновленную посылку
        updated = await self._repo.update(
            pkg_id,
            {"shipping_cost": cost},
        )
        return updated

    async def recalculate_all_pending(self) -> int:
        """
        Пересчитывает стоимость для всех посылок без shipping_cost.
        Возвращает количество отправленных задач.
        """
        logger.info("Starting bulk recalculation of pending packages")
        
        total, packages = await self._repo.list(has_cost=False, limit=1000)
        
        logger.info(f"Found {total} packages without shipping cost")
        
        tasks_sent = 0
        for package in packages:
            try:
                self._schedule_shipping_calculation(package.id)
                tasks_sent += 1
            except Exception as e:
                logger.error(f"Failed to schedule task for package {package.id}: {e}")
        
        logger.info(f"Successfully scheduled {tasks_sent} tasks for recalculation")
        return tasks_sent
