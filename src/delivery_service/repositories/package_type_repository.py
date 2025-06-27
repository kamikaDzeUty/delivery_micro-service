# src/delivery_service/repositories/package_type_repository.py
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

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
            raise RuntimeError(f"Database error while listing package types: {e}")

    async def create(self, name: str) -> PackageType:
        """
        Создаёт новый тип посылки.
        """
        try:
            result = PackageType(name=name)
            self.session.add(result)
            await self.session.commit()
            await self.session.refresh(result)
            return result
        except IntegrityError as e:
            await self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ValueError(f"Package type with name '{name}' already exists")
            raise RuntimeError(f"Database integrity error while creating package type: {e}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Database error while creating package type: {e}")

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
            raise RuntimeError(f"Database error while getting package type {type_id}: {e}")

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
            raise RuntimeError(f"Database error while getting package type by name '{name}': {e}")
