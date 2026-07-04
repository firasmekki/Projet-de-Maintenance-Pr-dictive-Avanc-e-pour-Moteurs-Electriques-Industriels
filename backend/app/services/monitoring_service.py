from collections.abc import Sequence
from uuid import UUID

from app.db.models.sensor_data import SensorData
from app.repositories.sensor_data_repository import SensorDataRepository


class MonitoringService:
    def __init__(self, sensor_data_repository: SensorDataRepository) -> None:
        self.sensor_data_repository = sensor_data_repository

    def get_latest_sensor_data(self, motor_id: UUID) -> SensorData | None:
        return self.sensor_data_repository.get_latest_sensor_data(motor_id)

    def get_sensor_history(self, motor_id: UUID, skip: int = 0, limit: int = 1000) -> Sequence[SensorData]:
        return self.sensor_data_repository.get_sensor_history(motor_id, skip=skip, limit=limit)
