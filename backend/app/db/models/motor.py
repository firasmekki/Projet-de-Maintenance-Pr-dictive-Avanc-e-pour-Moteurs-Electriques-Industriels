from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Motor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "motors"

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    rated_power_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rated_voltage: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rated_current: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rpm: Mapped[int] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)

    sensor_data: Mapped[list["SensorData"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    fault_history: Mapped[list["FaultHistory"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    maintenance_history: Mapped[list["MaintenanceHistory"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    predictions: Mapped[list["PredictionHistory"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
