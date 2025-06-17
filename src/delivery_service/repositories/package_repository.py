from uuid import UUID
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.models.package import Package

class PackageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, pkg: Package) -> Package:
        """
        Сохраняет новый объект Package в БД.
        """
        self.session.add(pkg)
        await self.session.commit()
        await self.session.refresh(pkg)
        return pkg

    async def get(self, pkg_id: UUID) -> Optional[Package]:
        """
        Возвращает одну посылку по UUID или None.
        """
        return await self.session.get(Package, pkg_id)

    async def list(
        self,
        *,
        type_id: Optional[UUID] = None,
        has_cost: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[int, List[Package]]:
        """
        Возвращает кортеж (total_count, items), где
        - total_count: общее число записей по фильтру
        - items: список Package
        """
        conditions = []
        if type_id is not None:
            conditions.append(Package.type_id == type_id)
        if has_cost is True:
            conditions.append(Package.shipping_cost.isnot(None))
        elif has_cost is False:
            conditions.append(Package.shipping_cost.is_(None))

        stmt = select(Package).where(*conditions)

        # общий счётчик
        total = (await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()

        # сами записи
        items = (await self.session.execute(
            stmt.limit(limit).offset(offset)
        )).scalars().all()

        return total, items

    async def update(self, pkg_id: UUID, pkg_data: dict) -> Optional[Package]:
        """
        Обновляет поля у посылки по ID.
        Pkg_data — словарь с изменёнными значениями.
        """
        pkg = await self.get(pkg_id)
        if pkg is None:
            return None

        for field, value in pkg_data.items():
            setattr(pkg, field, value)
            
        await self.session.commit()
        await self.session.refresh(pkg)
        return pkg

    async def delete(self, pkg_id: UUID) -> None:
        """
        Удаляет посылку по ID.
        """
        pkg = await self.get(pkg_id)
        if pkg:
            await self.session.delete(pkg)
            await self.session.commit()
