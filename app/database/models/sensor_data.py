import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    motor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core sensor readings
    temperature = Column(Float, nullable=True)       # Celsius
    vibration = Column(Float, nullable=True)         # mm/s RMS
    current = Column(Float, nullable=True)           # Amperes
    voltage = Column(Float, nullable=True)           # Volts
    power = Column(Float, nullable=True)             # Watts
    load_percentage = Column(Float, nullable=True)   # 0–100 %
    speed_rpm = Column(Float, nullable=True)

    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    source = Column(String(50), nullable=True, default="sensor")

    motor = relationship("Motor", back_populates="sensor_data")

    def __repr__(self) -> str:
        return (
            f"<SensorData motor={self.motor_id} "
            f"temp={self.temperature} vib={self.vibration} at={self.recorded_at}>"
        )
