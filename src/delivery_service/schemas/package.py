from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from src.delivery_service.schemas.package_type import PackageTypeRead

class PackageBase(BaseModel):
    name: str
    weight: Decimal
    declared_value: Decimal
    type_id: UUID

class PackageCreate(PackageBase):
    pass

class PackageUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[Decimal] = None
    declared_value: Optional[Decimal] = None
    type_id: Optional[UUID] = None

class PackageRead(PackageBase):
    id: UUID
    shipping_cost: Optional[Decimal]
    type: PackageTypeRead

    class Config:
        orm_mode = True

class PackageList(BaseModel):
    total: int
    items: List[PackageRead]
