from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class PackageTypeRead(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор типа посылки")
    name: str = Field(..., description="Название типа посылки")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Хрупкие предметы"
            }
        }
    }

class PackageTypeCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Название типа посылки"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация названия типа посылки"""
        if not v or not v.strip():
            raise ValueError('Название типа посылки не может быть пустым')
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Хрупкие предметы"
            }
        }
    }
