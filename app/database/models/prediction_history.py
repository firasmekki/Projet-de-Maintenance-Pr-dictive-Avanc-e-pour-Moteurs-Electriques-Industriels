import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    motor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Fault classification
    predicted_fault = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)

    # Health
    health_score = Column(Float, nullable=False)
    health_status = Column(String(20), nullable=False)  # Healthy | Warning | Critical

    # Risk horizons
    risk_score_7d = Column(Float, nullable=False, default=0.0)
    risk_score_30d = Column(Float, nullable=False, default=0.0)

    # Anomaly
    anomaly_detected = Column(Boolean, nullable=False, default=False)
    anomaly_score = Column(Float, nullable=True)

    # Metadata
    features_used = Column(JSONB, nullable=True)
    model_version = Column(String(50), nullable=True, default="1.0.0")

    prediction_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    motor = relationship("Motor", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<PredictionHistory motor={self.motor_id} "
            f"fault={self.predicted_fault} health={self.health_score:.1f}>"
        )
