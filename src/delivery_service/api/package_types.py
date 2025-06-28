from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body

from src.delivery_service.core.dependencies import get_package_type_repository
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
    logger.info("Получение всех типов посылок")
    
    try:
        package_types = await repo.list()
        logger.info(f"Получено {len(package_types)} типов посылок")
        return [PackageTypeRead.model_validate(pt) for pt in package_types]
    except Exception as e:
        logger.error(f"Ошибка при получении типов посылок: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/", response_model=PackageTypeRead)
async def create_package_type(
        payload: PackageTypeCreate = Body(..., description="Данные для создания типа посылки"),
        repo: PackageTypeRepository = Depends(get_package_type_repository)
) -> PackageTypeRead:
    """
    Создает новый тип посылки.
    """
    logger.info(f"Создание нового типа посылки: {payload.name}")
    
    try:
        package_type = await repo.create(payload.name)
        logger.info(f"Тип посылки успешно создан: {package_type.id} - {package_type.name}")
        return PackageTypeRead.model_validate(package_type)
    except Exception as e:
        logger.error(f"Ошибка при создании типа посылки '{payload.name}': {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")



