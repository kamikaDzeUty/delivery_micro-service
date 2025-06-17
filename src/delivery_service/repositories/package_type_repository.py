# src/delivery_service/repositories/package_type_repository.py
from uuid import UUID
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.models.package_type import PackageType

class PackageTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[PackageType]:
        """
        Возвращает все типы посылок.
        """
        result = await self.session.execute(select(PackageType))
        return result.scalars().all()

    async def get(self, id: UUID) -> Optional[PackageType]:
        """
        Возвращает один тип по ID или None.
        """
        return await self.session.get(PackageType, id)
