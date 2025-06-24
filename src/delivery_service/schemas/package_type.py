from uuid import UUID
from pydantic import BaseModel

class PackageTypeRead(BaseModel):
    id: UUID
    name: str

    model_config = {
        "from_attributes": True
    }

class PackageTypeCreate(BaseModel):
    name: str
