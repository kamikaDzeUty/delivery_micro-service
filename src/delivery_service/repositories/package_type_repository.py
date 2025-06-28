from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.delivery_service.models.package_type import PackageType


class PackageTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> Sequence[PackageType]:
        """
        Возвращает все типы посылок.
        """
        try:
            result = await self.session.execute(select(PackageType))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Ошибка базы данных при получении списка типов посылок: {e}"
            )

    async def create(self, name: str) -> PackageType:
        """
        Создает новый тип посылки.
        """
        try:
            package_type = PackageType(name=name)
            self.session.add(package_type)
            await self.session.commit()
            await self.session.refresh(package_type)
            return package_type
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(
                f"Ошибка базы данных при создании типа посылки '{name}': {e}"
            )

    async def get_by_id(self, type_id: str) -> PackageType | None:
        """
        Возвращает тип посылки по ID.
        """
        try:
            result = await self.session.execute(
                select(PackageType).where(PackageType.id == type_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Ошибка базы данных при получении типа посылки {type_id}: {e}"
            )

    async def get_by_name(self, name: str) -> PackageType | None:
        """
        Возвращает тип посылки по имени.
        """
        try:
            result = await self.session.execute(
                select(PackageType).where(PackageType.name == name)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Ошибка базы данных при получении типа посылки по имени '{name}': {e}"
            )
