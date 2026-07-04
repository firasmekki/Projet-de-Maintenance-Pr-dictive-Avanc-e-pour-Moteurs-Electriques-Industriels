from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin


class PredictionHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "prediction_history"
    __table_args__ = (
        Index("ix_prediction_history_motor_predicted_at", "motor_id", "predicted_at"),
    )

    motor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Fault classification output
    predicted_fault: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Health prediction output
    health_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), nullable=False)  # Healthy | Warning | Critical

    # Risk prediction output
    risk_score_7d: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    risk_score_30d: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    # Anomaly detection output
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anomaly_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    # Audit metadata
    features_used: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    motor: Mapped["Motor"] = relationship(back_populates="predictions")
