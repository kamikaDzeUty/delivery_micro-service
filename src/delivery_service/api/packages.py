from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.database import get_session
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.services.package_service import PackageService
from src.delivery_service.schemas.package import (
    PackageRead,
    PackageCreate,
    PackageList,
)

router = APIRouter(prefix="/packages", tags=["packages"])

def get_package_service(session: AsyncSession = Depends(get_session)) -> PackageService:
    repo = PackageRepository(session)
    return PackageService(repo)

@router.post("/", response_model=PackageRead, status_code=201)
async def create_package(
    payload: PackageCreate = Body(...),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Регистрирует новую посылку (без расчёта стоимости).
    """
    pkg = await service.create_package(payload)
    return PackageRead.model_validate(pkg)

@router.post("/{pkg_id}/calculate", response_model=PackageRead)
async def calculate_shipping_cost(
    pkg_id: UUID = Path(...),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Запускает расчёт стоимости для одной посылки.
    """
    pkg = await service.update_shipping_cost(pkg_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return PackageRead.model_validate(pkg)

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
    service  = Depends(get_package_service),
) -> PackageList:
    """
    Список посылок с пагинацией и фильтрацией по типу и наличию shipping_cost.
    """
    total, items = await service.list_packages(
        type_id=type_id,
        has_cost=calculated,
        limit=limit,
        offset=offset,
    )
    return PackageList(total=total, items=items)

@router.get("/{pkg_id}", response_model=PackageRead)
async def get_package(
    pkg_id: UUID = Path(...),
    service: PackageService = Depends(get_package_service),
) -> PackageRead:
    """
    Полные данные по одной посылке.
    """
    pkg = await service.get_package(pkg_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return PackageRead.model_validate(pkg)
