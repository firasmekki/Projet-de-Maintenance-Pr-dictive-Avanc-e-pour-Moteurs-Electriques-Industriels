from datetime import UTC, datetime
from decimal import Decimal

from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from app.services.health_score_service import HealthScoreService


def build_motor() -> Motor:
    return Motor(
        name="Test Motor",
        manufacturer="WEG",
        model="W22",
        rated_power_kw=Decimal("75.00"),
        rated_voltage=Decimal("415.00"),
        rated_current=Decimal("132.50"),
        rpm=1480,
        location="Test Bench",
        status="active",
    )


def build_sensor_data(
    motor: Motor,
    temperature: Decimal,
    vibration: Decimal,
    current: Decimal,
) -> SensorData:
    return SensorData(
        motor_id=motor.id,
        temperature=temperature,
        vibration=vibration,
        current=current,
        voltage=Decimal("415.000"),
        power=Decimal("70.000"),
        power_factor=Decimal("0.910"),
        thd=Decimal("3.200"),
        load=Decimal("82.000"),
        timestamp=datetime.now(UTC),
    )


def test_health_score_healthy() -> None:
    motor = build_motor()
    sensor_data = build_sensor_data(motor, Decimal("72.000"), Decimal("3.500"), Decimal("100.000"))

    result = HealthScoreService().calculate(motor, sensor_data)

    assert result.health_score == 100
    assert result.status == "Healthy"


def test_health_score_warning() -> None:
    motor = build_motor()
    sensor_data = build_sensor_data(motor, Decimal("95.000"), Decimal("3.500"), Decimal("100.000"))

    result = HealthScoreService().calculate(motor, sensor_data)

    assert result.health_score == 80
    assert result.status == "Healthy"


def test_health_score_critical() -> None:
    motor = build_motor()
    sensor_data = build_sensor_data(motor, Decimal("95.000"), Decimal("8.500"), Decimal("150.000"))

    result = HealthScoreService().calculate(motor, sensor_data)

    assert result.health_score == 45
    assert result.status == "Critical"
