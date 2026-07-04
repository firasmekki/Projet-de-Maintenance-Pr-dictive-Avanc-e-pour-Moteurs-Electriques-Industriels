from decimal import Decimal

from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from app.schemas.monitoring import HealthResponse


class HealthScoreService:
    def calculate(self, motor: Motor, latest_sensor_data: SensorData) -> HealthResponse:
        score = 100

        if latest_sensor_data.temperature > Decimal("90"):
            score -= 20

        if latest_sensor_data.vibration > Decimal("7"):
            score -= 20

        if latest_sensor_data.current > motor.rated_current:
            score -= 15

        score = max(score, 0)

        return HealthResponse(
            health_score=score,
            status=self._status_for_score(score),
        )

    @staticmethod
    def _status_for_score(score: int) -> str:
        if score >= 80:
            return "Healthy"
        if score >= 60:
            return "Warning"
        return "Critical"
