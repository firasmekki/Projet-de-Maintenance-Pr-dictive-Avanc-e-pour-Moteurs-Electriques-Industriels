from datetime import UTC, datetime
from decimal import Decimal

from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from app.schemas.diagnostics import TrendAnalysisResponse, TrendWindowResponse
from app.services.fault_scoring_service import FaultScoringService


def motor() -> Motor:
    return Motor(
        name="Diagnostic Test Motor",
        manufacturer="ABB",
        model="M3BP",
        rated_power_kw=Decimal("75.00"),
        rated_voltage=Decimal("415.00"),
        rated_current=Decimal("100.00"),
        rpm=1480,
        location="Test Stand",
        status="active",
    )


def sensor(
    motor_instance: Motor,
    temperature: str,
    vibration: str,
    current: str,
    load: str = "80.000",
) -> SensorData:
    return SensorData(
        motor_id=motor_instance.id,
        temperature=Decimal(temperature),
        vibration=Decimal(vibration),
        current=Decimal(current),
        voltage=Decimal("415.000"),
        power=Decimal("70.000"),
        power_factor=Decimal("0.910"),
        thd=Decimal("3.000"),
        load=Decimal(load),
        timestamp=datetime.now(UTC),
    )


def stable_trends() -> TrendAnalysisResponse:
    stable = TrendWindowResponse(temperature="STABLE", vibration="STABLE", current="STABLE")
    return TrendAnalysisResponse(last_24h=stable, last_7d=stable, last_30d=stable)


def test_detects_bearing_wear() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "95.000", "6.800", "96.000"), stable_trends())

    assert result.fault == "Bearing Wear"
    assert result.severity == "HIGH"
    assert result.confidence == 80


def test_detects_misalignment() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "82.000", "8.200", "92.000"), stable_trends())

    assert result.fault == "Misalignment"
    assert result.severity == "HIGH"


def test_detects_unbalance() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "72.000", "6.700", "90.000"), stable_trends())

    assert result.fault == "Unbalance"
    assert result.severity == "HIGH"


def test_detects_rotor_fault() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "82.000", "4.500", "110.000"), stable_trends())

    assert result.fault == "Rotor Fault"
    assert result.severity == "HIGH"


def test_detects_insulation_fault() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "96.000", "2.000", "110.000"), stable_trends())

    assert result.fault == "Insulation Fault"
    assert result.severity == "CRITICAL"


def test_detects_overload() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "96.000", "4.000", "120.000", "104.000"), stable_trends())

    assert result.fault == "Overload"
    assert result.severity == "CRITICAL"


def test_returns_no_fault_when_confidence_is_low() -> None:
    m = motor()
    result = FaultScoringService().score(m, sensor(m, "70.000", "2.000", "80.000"), stable_trends())

    assert result.fault == "No Fault Detected"
    assert result.severity == "LOW"
