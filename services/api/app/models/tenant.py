from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(
        Enum(
            "Start-up",
            "Enterprise",
            "Non-profit",
            "Government",
            "Mid-size",
            "Small Business",
            name="tenant_type",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
