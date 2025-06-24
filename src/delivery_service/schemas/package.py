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


class PackageRead(PackageBase):
    id: UUID
    shipping_cost: Optional[Decimal]
    type: PackageTypeRead

    model_config = {
        "from_attributes": True
    }


class PackageList(BaseModel):
    total: int
    items: List[PackageRead]
