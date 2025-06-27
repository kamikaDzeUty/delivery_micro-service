from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from src.delivery_service.models.package import Package
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.services.shipping_service import ShippingService


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

    async def create_package(self, pkg: Package) -> Package:
        # простая передача в репозиторий
        return await self._repo.create(pkg)

    async def get_package(self, pkg_id: UUID) -> Optional[Package]:
        return await self._repo.get(pkg_id)

    async def list_packages(
        self,
        *,
        type_id: Optional[UUID] = None,
        has_cost: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, Sequence[Package]]:
        return await self._repo.list(
            type_id=type_id,
            has_cost=has_cost,
            limit=limit,
            offset=offset,
        )

    async def update_shipping_cost(self, pkg_id: UUID) -> Optional[Decimal]:
        """
        Пересчитывает и сохраняет shipping_cost у посылки.
        Возвращает новую стоимость или None, если посылки нет.
        """
        pkg = await self._repo.get(pkg_id)
        if pkg is None:
            return None

        cost = await self._shipping.calculate_shipping_cost(
            weight_kg=pkg.weight,
            declared_value_usd=pkg.declared_value,
        )
        # сохраняем только одно поле
        updated = await self._repo.update(
            pkg_id,
            {"shipping_cost": cost},
        )
        return getattr(updated, "shipping_cost", None)
