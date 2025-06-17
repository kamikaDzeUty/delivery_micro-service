from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.database import get_session
from src.delivery_service.repositories.package_type_repository import PackageTypeRepository
from src.delivery_service.schemas.package_type import PackageTypeRead

router = APIRouter(prefix="/package-types", tags=["package-types"])

@router.get("/", response_model=List[PackageTypeRead])
async def list_package_types(session: AsyncSession = Depends(get_session)) -> List[PackageTypeRead]:
    """
    Возвращает весь справочник типов посылок.
    """
    repo = PackageTypeRepository(session)
    types = await repo.list()
    return types
