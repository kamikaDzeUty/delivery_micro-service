from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from src.delivery_service.schemas.package_type import PackageTypeRead

class PackageBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Название посылки"
    )
    weight: Decimal = Field(
        ..., 
        gt=0, 
        le=1000,
        description="Вес посылки в килограммах (0-1000 кг)"
    )
    declared_value: Decimal = Field(
        ..., 
        ge=0, 
        le=1000000,
        description="Объявленная стоимость в USD (0-1,000,000 USD)"
    )
    type_id: UUID = Field(..., description="ID типа посылки")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация названия посылки"""
        if not v or not v.strip():
            raise ValueError('Название посылки не может быть пустым')
        return v.strip()

    @field_validator('weight')
    @classmethod
    def validate_weight(cls, v: Decimal) -> Decimal:
        """Валидация веса посылки"""
        if v <= 0:
            raise ValueError('Вес посылки должен быть больше 0')
        if v > 1000:
            raise ValueError('Вес посылки не может превышать 1000 кг')
        return v

    @field_validator('declared_value')
    @classmethod
    def validate_declared_value(cls, v: Decimal) -> Decimal:
        """Валидация объявленной стоимости"""
        if v < 0:
            raise ValueError('Объявленная стоимость не может быть отрицательной')
        if v > 1000000:
            raise ValueError('Объявленная стоимость не может превышать 1,000,000 USD')
        return v


class PackageCreate(PackageBase):
    pass


class PackageRead(PackageBase):
    id: UUID = Field(..., description="Уникальный идентификатор посылки")
    shipping_cost: Optional[Decimal] = Field(
        None, 
        ge=0,
        description="Стоимость доставки в рублях"
    )
    type: PackageTypeRead = Field(..., description="Тип посылки")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Электроника",
                "weight": "2.5",
                "declared_value": "500.00",
                "shipping_cost": "7500.50",
                "type_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Хрупкие предметы"
                }
            }
        }
    }


class PackageList(BaseModel):
    total: int = Field(..., ge=0, description="Общее количество посылок")
    items: List[PackageRead] = Field(..., description="Список посылок")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Электроника",
                        "weight": "2.5",
                        "declared_value": "500.00",
                        "shipping_cost": "7500.50",
                        "type_id": "123e4567-e89b-12d3-a456-426614174001",
                        "type": {
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "name": "Хрупкие предметы"
                        }
                    }
                ]
            }
        }
    }
