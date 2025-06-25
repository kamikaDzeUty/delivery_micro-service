# src/delivery_service/repositories/package_type_repository.py
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.models.package_type import PackageType

class PackageTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> Sequence[PackageType]:
        """
        Возвращает все типы посылок.
        """
        result = await self.session.execute(select(PackageType))
        return result.scalars().all()

    async def create(self, name: str) -> PackageType:
        """
        Создаёт новый тип посылки.
        """
        result = PackageType(name=name)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result
