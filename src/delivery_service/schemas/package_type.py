from uuid import UUID
from pydantic import BaseModel

class PackageTypeRead(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True
