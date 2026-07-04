from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from statistics import mean
from uuid import UUID

from app.db.models.sensor_data import SensorData
from app.repositories.sensor_data_repository import SensorDataRepository
from app.schemas.diagnostics import TrendAnalysisResponse, TrendWindowResponse


class TrendAnalysisService:
    def __init__(self, sensor_data_repository: SensorDataRepository) -> None:
        self.sensor_data_repository = sensor_data_repository

    def analyze(self, motor_id: UUID) -> TrendAnalysisResponse:
        return TrendAnalysisResponse(
            last_24h=self._analyze_window(motor_id, timedelta(hours=24)),
            last_7d=self._analyze_window(motor_id, timedelta(days=7)),
            last_30d=self._analyze_window(motor_id, timedelta(days=30)),
        )

    def _analyze_window(self, motor_id: UUID, window: timedelta) -> TrendWindowResponse:
        since = datetime.now(UTC) - window
        records = list(self.sensor_data_repository.get_sensor_history_since(motor_id, since))

        return TrendWindowResponse(
            temperature=self._indicator(records, "temperature"),
            vibration=self._indicator(records, "vibration"),
            current=self._indicator(records, "current"),
        )

    @staticmethod
    def _indicator(records: Sequence[SensorData], field: str) -> str:
        if len(records) < 4:
            return "STABLE"

        midpoint = len(records) // 2
        first_half = records[:midpoint]
        second_half = records[midpoint:]
        first_avg = mean(float(getattr(record, field)) for record in first_half)
        second_avg = mean(float(getattr(record, field)) for record in second_half)

        if first_avg == 0:
            return "STABLE"

        change = Decimal(str((second_avg - first_avg) / first_avg))
        if change >= Decimal("0.05"):
            return "RISING"
        if change <= Decimal("-0.05"):
            return "FALLING"
        return "STABLE"
