import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Motor(Base):
    __tablename__ = "motors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(200), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    location = Column(String(300), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    model_number = Column(String(100), nullable=True)

    # Electrical specs
    rated_power_kw = Column(Float, nullable=False)
    rated_current = Column(Float, nullable=False)   # Amperes
    rated_voltage = Column(Float, nullable=False)   # Volts
    rated_speed_rpm = Column(Integer, nullable=True)
    power_factor = Column(Float, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    installation_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sensor_data = relationship("SensorData", back_populates="motor", cascade="all, delete-orphan")
    fault_history = relationship("FaultHistory", back_populates="motor", cascade="all, delete-orphan")
    maintenance_history = relationship("MaintenanceHistory", back_populates="motor", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="motor", cascade="all, delete-orphan")
    predictions = relationship("PredictionHistory", back_populates="motor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Motor {self.name} sn={self.serial_number}>"
