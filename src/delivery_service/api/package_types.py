from typing import List, Sequence
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.database import get_session
from src.delivery_service.models import PackageType
from src.delivery_service.repositories.package_type_repository import PackageTypeRepository
from src.delivery_service.schemas.package_type import PackageTypeRead, PackageTypeCreate

router = APIRouter(prefix="/package-types", tags=["package-types"])

@router.get("/", response_model=List[PackageTypeRead])
async def list_package_types(
        session: AsyncSession = Depends(get_session)
) -> Sequence[PackageType]:
    """
    Возвращает весь справочник типов посылок.
    """
    repo = PackageTypeRepository(session)
    return await repo.list()

@router.post("/", response_model=PackageTypeRead)
async def create_package_type(
        payload: PackageTypeCreate,
        session: AsyncSession = Depends(get_session)
) -> PackageType:
    """
    Создает новый тип посылки.
    """
    repo = PackageTypeRepository(session)
    return await repo.create(payload.name)



