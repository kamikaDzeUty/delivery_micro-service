# src/delivery_service/models/package.py
import uuid
from sqlalchemy import Column, String, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import Base

class Package(Base):
    __tablename__ = "packages"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           = Column(String(100), nullable=False)
    weight         = Column(Numeric(10, 3), nullable=False)
    declared_value = Column(Numeric(12, 2), nullable=False)
    shipping_cost  = Column(Numeric(12, 2), nullable=True)

    type_id = Column(UUID(as_uuid=True), ForeignKey("package_types.id"), nullable=False)
    type    = relationship("PackageType", back_populates="packages")
