from typing import List, Sequence
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.dependencies import get_package_type_repository
from src.delivery_service.models import PackageType
from src.delivery_service.repositories.package_type_repository import PackageTypeRepository
from src.delivery_service.schemas.package_type import PackageTypeRead, PackageTypeCreate
from src.delivery_service.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/package-types", tags=["package-types"])

@router.get("/", response_model=List[PackageTypeRead])
async def list_package_types(
        repo: PackageTypeRepository = Depends(get_package_type_repository)
) -> List[PackageTypeRead]:
    """
    Возвращает весь справочник типов посылок.
    """
    logger.info("Listing all package types")
    
    try:
        package_types = await repo.list()
        logger.info(f"Retrieved {len(package_types)} package types")
        return [PackageTypeRead.model_validate(pt) for pt in package_types]
    except Exception as e:
        logger.error(f"Failed to list package types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=PackageTypeRead)
async def create_package_type(
        payload: PackageTypeCreate = Body(..., description="Данные для создания типа посылки"),
        repo: PackageTypeRepository = Depends(get_package_type_repository)
) -> PackageTypeRead:
    """
    Создает новый тип посылки.
    """
    logger.info(f"Creating new package type: {payload.name}")
    
    try:
        package_type = await repo.create(payload.name)
        logger.info(f"Package type created successfully: {package_type.id} - {package_type.name}")
        return PackageTypeRead.model_validate(package_type)
    except Exception as e:
        logger.error(f"Failed to create package type '{payload.name}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



