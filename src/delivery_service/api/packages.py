from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from src.delivery_service.core.dependencies import get_package_service
from src.delivery_service.services.package_service import PackageService
from src.delivery_service.schemas.package import (
    PackageRead,
    PackageCreate,
    PackageList,
)
from src.delivery_service.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/packages", tags=["packages"])

@router.post("/", response_model=PackageRead, status_code=201)
async def create_package(
    payload: PackageCreate = Body(...),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Регистрирует новую посылку и автоматически запускает расчет стоимости через Celery.
    """
    logger.info(f"Создание посылки: {payload.name} (вес: {payload.weight}кг, стоимость: ${payload.declared_value})")
    
    try:
        pkg = await service.create_package(payload)
        logger.info(f"Посылка успешно создана: {pkg.id}")
        return PackageRead.model_validate(pkg)
    except Exception as e:
        logger.error(f"Ошибка при создании посылки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/{pkg_id}/calculate", response_model=PackageRead)
async def calculate_shipping_cost(
    pkg_id: UUID = Path(..., description="ID посылки для расчета стоимости"),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Запускает расчёт стоимости для одной посылки (синхронно).
    """
    logger.info(f"Расчет стоимости доставки для посылки: {pkg_id}")
    
    try:
        pkg = await service.update_shipping_cost(pkg_id)
        if pkg is None:
            logger.warning(f"Посылка не найдена для расчета: {pkg_id}")
            raise HTTPException(status_code=404, detail="Посылка не найдена")
        
        logger.info(f"Стоимость доставки успешно рассчитана для посылки {pkg_id}: {pkg.shipping_cost}")
        return PackageRead.model_validate(pkg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при расчете стоимости доставки для посылки {pkg_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/recalculate-pending")
async def recalculate_all_pending_packages(
    service: PackageService = Depends(get_package_service),
) -> dict:
    """
    Запускает пересчет стоимости для всех посылок без shipping_cost через Celery.
    """
    logger.info("Запуск массового пересчета ожидающих посылок")
    
    try:
        tasks_sent = await service.recalculate_all_pending()
        logger.info(f"Массовый пересчет завершен: запланировано {tasks_sent} задач")
        return {
            "message": f"Запланировано {tasks_sent} задач для пересчета",
            "tasks_sent": tasks_sent
        }
    except Exception as e:
        logger.error(f"Ошибка при запуске массового пересчета: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/", response_model=PackageList)
async def list_packages(
    type_id: Optional[UUID]    = Query(None, description="Фильтр по типу"),
    calculated: Optional[bool] = Query(
        None,
        alias="calculated",
        description="True — только с рассчитанной стоимостью; False — только без"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Макс число записей"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    service: PackageService = Depends(get_package_service),
) -> PackageList:
    """
    Список посылок с пагинацией и фильтрацией по типу и наличию shipping_cost.
    """
    logger.info(f"Получение списка посылок: type_id={type_id}, calculated={calculated}, limit={limit}, offset={offset}")
    
    try:
        total, items = await service.list_packages(
            type_id=type_id,
            has_cost=calculated,
            limit=limit,
            offset=offset,
        )
        
        # Конвертируем ORM модели в Pydantic схемы
        package_reads = [PackageRead.model_validate(item) for item in items]
        
        logger.info(f"Получено {len(package_reads)} посылок из {total} всего")
        return PackageList(total=total, items=package_reads)
    except Exception as e:
        logger.error(f"Ошибка при получении списка посылок: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{pkg_id}", response_model=PackageRead)
async def get_package(
    pkg_id: UUID = Path(..., description="ID посылки"),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Полные данные по одной посылке.
    """
    logger.info(f"Получение деталей посылки: {pkg_id}")
    
    try:
        pkg = await service.get_package(pkg_id)
        if pkg is None:
            logger.warning(f"Посылка не найдена: {pkg_id}")
            raise HTTPException(status_code=404, detail="Посылка не найдена")
        
        logger.info(f"Посылка успешно получена: {pkg_id}")
        return PackageRead.model_validate(pkg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении посылки {pkg_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
