from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, select

from app.db.models.sensor_data import SensorData
from app.repositories.base import BaseRepository


class SensorDataRepository(BaseRepository[SensorData]):
    model = SensorData

    def get_latest_for_motor(self, motor_id: UUID, limit: int = 100) -> Sequence[SensorData]:
        statement = (
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(desc(SensorData.timestamp))
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def get_latest_sensor_data(self, motor_id: UUID) -> SensorData | None:
        statement = (
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(desc(SensorData.timestamp))
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def get_sensor_history(self, motor_id: UUID, skip: int = 0, limit: int = 1000) -> Sequence[SensorData]:
        statement = (
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(desc(SensorData.timestamp))
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def get_sensor_history_since(self, motor_id: UUID, since: datetime) -> Sequence[SensorData]:
        statement = (
            select(SensorData)
            .where(SensorData.motor_id == motor_id, SensorData.timestamp >= since)
            .order_by(SensorData.timestamp.asc())
        )
        return self.db.scalars(statement).all()
