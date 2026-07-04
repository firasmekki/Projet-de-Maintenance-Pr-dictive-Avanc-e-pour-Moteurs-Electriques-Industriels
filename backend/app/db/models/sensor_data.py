from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin


class SensorData(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sensor_data"
    __table_args__ = (
        Index("ix_sensor_data_motor_timestamp", "motor_id", "timestamp"),
    )

    motor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    temperature: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    vibration: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    current: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    voltage: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    power: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    power_factor: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    thd: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    load: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    motor: Mapped["Motor"] = relationship(back_populates="sensor_data")
