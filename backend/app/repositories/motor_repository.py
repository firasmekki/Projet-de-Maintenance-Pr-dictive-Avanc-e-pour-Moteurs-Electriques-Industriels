from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select

from app.db.models.fault_history import FaultHistory
from app.db.models.maintenance_history import MaintenanceHistory
from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from app.repositories.base import BaseRepository


class MotorRepository(BaseRepository[Motor]):
    model = Motor

    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> Sequence[Motor]:
        statement = select(Motor).where(Motor.status == status).offset(skip).limit(limit)
        return self.db.scalars(statement).all()

    def get_motor_with_stats(self, motor_id: UUID) -> dict[str, object] | None:
        motor = self.get_by_id(motor_id)
        if motor is None:
            return None

        latest_sensor_data = self.db.scalars(
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(SensorData.timestamp.desc())
            .limit(1)
        ).first()
        total_faults = self.db.scalar(
            select(func.count(FaultHistory.id)).where(FaultHistory.motor_id == motor_id)
        )
        total_maintenance_events = self.db.scalar(
            select(func.count(MaintenanceHistory.id)).where(MaintenanceHistory.motor_id == motor_id)
        )

        return {
            "motor": motor,
            "latest_sensor_data": latest_sensor_data,
            "total_faults": int(total_faults or 0),
            "total_maintenance_events": int(total_maintenance_events or 0),
        }
