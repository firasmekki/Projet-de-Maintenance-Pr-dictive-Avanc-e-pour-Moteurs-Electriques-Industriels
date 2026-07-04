from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin


class MaintenanceHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "maintenance_history"

    motor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    maintenance_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_by: Mapped[str] = mapped_column(String(120), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    motor: Mapped["Motor"] = relationship(back_populates="maintenance_history")
