from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MotorResponse(BaseModel):
    id: UUID
    name: str
    manufacturer: str
    model: str
    location: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class SensorDataResponse(BaseModel):
    id: UUID
    motor_id: UUID
    temperature: Decimal
    vibration: Decimal
    current: Decimal
    voltage: Decimal
    power: Decimal
    power_factor: Decimal
    thd: Decimal
    load: Decimal
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorDataListResponse(BaseModel):
    motor_id: UUID
    count: int
    items: list[SensorDataResponse]


class LatestSensorDataResponse(BaseModel):
    motor_id: UUID
    latest: SensorDataResponse


class HealthResponse(BaseModel):
    health_score: int = Field(ge=0, le=100)
    status: str


class MotorDetailsResponse(BaseModel):
    id: UUID
    name: str
    manufacturer: str
    model: str
    rated_power_kw: Decimal
    rated_voltage: Decimal
    rated_current: Decimal
    rpm: int
    location: str
    status: str
    created_at: datetime
    updated_at: datetime
    latest_sensor_values: SensorDataResponse | None
    total_faults: int
    total_maintenance_events: int

    model_config = ConfigDict(from_attributes=True)
