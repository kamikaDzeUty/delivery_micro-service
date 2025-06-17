import uuid
from typing import Optional, Tuple

from src.delivery_service.models.package import Package
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.schemas.package import PackageCreate, PackageUpdate
from src.delivery_service.services.shipping_service import calculate_shipping_cost

class PackageService:
    def __init__(self, repo: PackageRepository):
        self.repo = repo

    async def create_package(self, data: PackageCreate) -> Package:
        pkg = Package(**data.dict(), shipping_cost=None)
        return await self.repo.create(pkg)

    async def get_package(self, pkg_id: uuid.UUID) -> Optional[Package]:
        return await self.repo.get(pkg_id)

    async def list_packages(
        self,
        *,
        type_id: Optional[uuid.UUID],
        has_cost: Optional[bool],
        limit: int,
        offset: int,
    ) -> Tuple[int, list[Package]]:
        return await self.repo.list(
            type_id=type_id, has_cost=has_cost, limit=limit, offset=offset
        )

    async def update_shipping_cost(self, pkg_id: uuid.UUID) -> Optional[Package]:
        pkg = await self.repo.get(pkg_id)
        if not pkg:
            return None
        cost = await calculate_shipping_cost(
            weight=pkg.weight, declared_value=pkg.declared_value
        )
        return await self.repo.update(pkg_id, {"shipping_cost": cost})

    async def update_package(
        self, pkg_id: uuid.UUID, data: PackageUpdate
    ) -> Optional[Package]:
        return await self.repo.update(pkg_id, data.dict(exclude_unset=True))

    async def delete_package(self, pkg_id: uuid.UUID) -> None:
        await self.repo.delete(pkg_id)
