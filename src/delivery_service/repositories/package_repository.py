from uuid import UUID
from typing import Optional, Any, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from src.delivery_service.models.package import Package

class PackageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, pkg: Package) -> Package:
        """
        Сохраняет новый объект Package в БД и подгружает связанные данные.
        """
        try:
            self.session.add(pkg)
            await self.session.commit()
            await self.session.refresh(pkg)

            stmt = (
                select(Package)
                .options(selectinload(Package.type))
                .where(Package.id == pkg.id)
            )
            result = await self.session.execute(stmt)
            pkg_with_type = result.scalar_one_or_none()

            if pkg_with_type is None:
                raise RuntimeError(f"Посылка с id {pkg.id} не найдена после вставки")

            return pkg_with_type
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Ошибка базы данных при создании посылки: {e}")

    async def get(self, pkg_id: UUID) -> Optional[Package]:
        """
        Возвращает одну посылку по UUID или None.
        """
        try:
            stmt = (
                select(Package)
                .where(Package.id == pkg_id)
                .options(selectinload(Package.type))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Ошибка базы данных при получении посылки {pkg_id}: {e}")

    async def list(
        self,
        *,
        type_id: Optional[UUID] = None,
        has_cost: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, Sequence[Package]]:
        """
        Возвращает кортеж (total_count, items), где
        - total_count: общее число записей по фильтру
        - items: список Package
        """
        try:
            conditions = []
            if type_id is not None:
                conditions.append(Package.type_id == type_id)
            if has_cost is True:
                conditions.append(Package.shipping_cost.isnot(None))
            elif has_cost is False:
                conditions.append(Package.shipping_cost.is_(None))

            stmt = select(Package).where(*conditions).options(selectinload(Package.type))

            # общий счётчик
            total = (await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )).scalar_one()

            # сами записи
            items = (await self.session.execute(
                stmt.limit(limit).offset(offset)
            )).scalars().all()

            return total, items
        except SQLAlchemyError as e:
            raise RuntimeError(f"Ошибка базы данных при получении списка посылок: {e}")

    async def update(self, pkg_id: UUID, pkg_data: dict[str, Any]) -> Optional[Package]:
        """
        Обновляет поля у посылки по ID.
        Pkg_data — словарь с изменёнными значениями.
        """
        try:
            pkg = await self.get(pkg_id)
            if pkg is None:
                return None

            for field, value in pkg_data.items():
                if hasattr(pkg, field):
                    setattr(pkg, field, value)
                else:
                    raise ValueError(f"Некорректное поле '{field}' для модели Package")
                
            await self.session.commit()
            await self.session.refresh(pkg)
            return pkg
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Ошибка базы данных при обновлении посылки {pkg_id}: {e}")

    async def delete(self, pkg_id: UUID) -> bool:
        """
        Удаляет посылку по ID.
        Возвращает True если посылка была удалена, False если не найдена.
        """
        try:
            pkg = await self.get(pkg_id)
            if pkg is None:
                return False

            await self.session.delete(pkg)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Ошибка базы данных при удалении посылки {pkg_id}: {e}")
