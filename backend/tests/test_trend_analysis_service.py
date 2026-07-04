from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.motor_repository import MotorRepository
from app.repositories.sensor_data_repository import SensorDataRepository
from app.services.trend_analysis_service import TrendAnalysisService


def test_trend_analysis_reports_rising_stable_and_falling(db_session: Session) -> None:
    motor = MotorRepository(db_session).create(
        {
            "name": "Trend Motor",
            "manufacturer": "WEG",
            "model": "W22",
            "rated_power_kw": Decimal("75.00"),
            "rated_voltage": Decimal("415.00"),
            "rated_current": Decimal("100.00"),
            "rpm": 1480,
            "location": "Trend Lab",
            "status": "active",
        }
    )
    sensor_repository = SensorDataRepository(db_session)
    start = datetime.now(UTC) - timedelta(hours=20)

    for index in range(10):
        sensor_repository.create(
            {
                "motor_id": motor.id,
                "temperature": Decimal(60 + index * 2),
                "vibration": Decimal("4.000"),
                "current": Decimal(100 - index * 2),
                "voltage": Decimal("415.000"),
                "power": Decimal("70.000"),
                "power_factor": Decimal("0.900"),
                "thd": Decimal("3.000"),
                "load": Decimal("80.000"),
                "timestamp": start + timedelta(hours=index * 2),
            }
        )

    trends = TrendAnalysisService(sensor_repository).analyze(motor.id)

    assert trends.last_24h.temperature == "RISING"
    assert trends.last_24h.vibration == "STABLE"
    assert trends.last_24h.current == "FALLING"
