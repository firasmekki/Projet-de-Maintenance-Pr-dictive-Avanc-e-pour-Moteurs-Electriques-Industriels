from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.fault_repository import FaultRepository
from app.repositories.motor_repository import MotorRepository
from app.repositories.sensor_data_repository import SensorDataRepository


def seed_diagnostic_motor(db_session: Session):
    motor = MotorRepository(db_session).create(
        {
            "name": "Diagnostic API Motor",
            "manufacturer": "WEG",
            "model": "W22",
            "rated_power_kw": Decimal("75.00"),
            "rated_voltage": Decimal("415.00"),
            "rated_current": Decimal("100.00"),
            "rpm": 1480,
            "location": "Diagnostic Cell",
            "status": "active",
        }
    )
    sensor_repository = SensorDataRepository(db_session)
    start = datetime.now(UTC) - timedelta(days=2)
    for index in range(8):
        sensor_repository.create(
            {
                "motor_id": motor.id,
                "temperature": Decimal(75 + index * 3),
                "vibration": Decimal("6.800"),
                "current": Decimal("96.000"),
                "voltage": Decimal("415.000"),
                "power": Decimal("70.000"),
                "power_factor": Decimal("0.910"),
                "thd": Decimal("3.000"),
                "load": Decimal("82.000"),
                "timestamp": start + timedelta(hours=index * 6),
            }
        )
    return motor


def test_post_diagnose_persists_fault_history(client: TestClient, db_session: Session) -> None:
    motor = seed_diagnostic_motor(db_session)

    response = client.post(f"/api/v1/diagnose/{motor.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["motor_id"] == str(motor.id)
    assert payload["fault"] == "Bearing Wear"
    assert payload["severity"] in {"HIGH", "CRITICAL"}
    assert payload["confidence"] >= 80
    assert payload["risk_level"] == payload["severity"]
    assert "Inspect bearing" in payload["recommendation"]

    faults = FaultRepository(db_session).get_for_motor(motor.id)
    assert len(faults) == 1
    assert faults[0].fault_type == "Bearing Wear"
    assert faults[0].confidence >= Decimal("80.00")


def test_get_faults_returns_fault_history(client: TestClient, db_session: Session) -> None:
    motor = seed_diagnostic_motor(db_session)
    client.post(f"/api/v1/diagnose/{motor.id}")

    response = client.get(f"/api/v1/motors/{motor.id}/faults")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["fault_type"] == "Bearing Wear"


def test_get_diagnosis_does_not_persist_fault_history(client: TestClient, db_session: Session) -> None:
    motor = seed_diagnostic_motor(db_session)

    response = client.get(f"/api/v1/motors/{motor.id}/diagnosis")

    assert response.status_code == 200
    assert response.json()["fault"] == "Bearing Wear"
    assert FaultRepository(db_session).get_for_motor(motor.id) == []
