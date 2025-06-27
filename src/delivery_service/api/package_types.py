from typing import List, Sequence
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.dependencies import get_package_type_repository
from src.delivery_service.models import PackageType
from src.delivery_service.repositories.package_type_repository import PackageTypeRepository
from src.delivery_service.schemas.package_type import PackageTypeRead, PackageTypeCreate

router = APIRouter(prefix="/package-types", tags=["package-types"])

@router.get("/", response_model=List[PackageTypeRead])
async def list_package_types(
        repo: PackageTypeRepository = Depends(get_package_type_repository)
) -> List[PackageTypeRead]:
    """
    Возвращает весь справочник типов посылок.
    """
    package_types = await repo.list()
    return [PackageTypeRead.model_validate(pt) for pt in package_types]

@router.post("/", response_model=PackageTypeRead)
async def create_package_type(
        payload: PackageTypeCreate,
        repo: PackageTypeRepository = Depends(get_package_type_repository)
) -> PackageTypeRead:
    """
    Создает новый тип посылки.
    """
    package_type = await repo.create(payload.name)
    return PackageTypeRead.model_validate(package_type)



