from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.fault_repository import FaultRepository
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.motor_repository import MotorRepository
from app.repositories.sensor_data_repository import SensorDataRepository


def seed_api_motor(db_session: Session):
    motor = MotorRepository(db_session).create(
        {
            "name": "API Test Motor",
            "manufacturer": "Siemens",
            "model": "SIMOTICS SD",
            "rated_power_kw": Decimal("110.00"),
            "rated_voltage": Decimal("415.00"),
            "rated_current": Decimal("195.00"),
            "rpm": 1485,
            "location": "Test Cell",
            "status": "active",
        }
    )
    sensor_repository = SensorDataRepository(db_session)
    older = sensor_repository.create(
        {
            "motor_id": motor.id,
            "temperature": Decimal("72.000"),
            "vibration": Decimal("3.200"),
            "current": Decimal("150.000"),
            "voltage": Decimal("414.000"),
            "power": Decimal("92.000"),
            "power_factor": Decimal("0.900"),
            "thd": Decimal("3.100"),
            "load": Decimal("78.000"),
            "timestamp": datetime.now(UTC) - timedelta(hours=1),
        }
    )
    latest = sensor_repository.create(
        {
            "motor_id": motor.id,
            "temperature": Decimal("95.000"),
            "vibration": Decimal("8.000"),
            "current": Decimal("210.000"),
            "voltage": Decimal("416.000"),
            "power": Decimal("135.000"),
            "power_factor": Decimal("0.890"),
            "thd": Decimal("5.200"),
            "load": Decimal("104.000"),
            "timestamp": datetime.now(UTC),
        }
    )
    FaultRepository(db_session).create(
        {
            "motor_id": motor.id,
            "fault_type": "Overload",
            "severity": "high",
            "confidence": Decimal("88.00"),
            "description": "Current exceeded nameplate rating.",
            "detected_at": datetime.now(UTC),
        }
    )
    MaintenanceRepository(db_session).create(
        {
            "motor_id": motor.id,
            "maintenance_type": "Inspection",
            "description": "Visual inspection completed.",
            "performed_by": "Reliability Team",
            "performed_at": datetime.now(UTC),
            "next_due_at": datetime.now(UTC) + timedelta(days=30),
        }
    )
    return motor, older, latest


def test_list_motors(client: TestClient, db_session: Session) -> None:
    motor, _, _ = seed_api_motor(db_session)

    response = client.get("/api/v1/motors")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(motor.id)
    assert payload[0]["name"] == "API Test Motor"
    assert "rated_current" not in payload[0]


def test_get_motor_details(client: TestClient, db_session: Session) -> None:
    motor, _, latest = seed_api_motor(db_session)

    response = client.get(f"/api/v1/motors/{motor.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(motor.id)
    assert payload["latest_sensor_values"]["id"] == str(latest.id)
    assert payload["total_faults"] == 1
    assert payload["total_maintenance_events"] == 1


def test_get_sensor_history(client: TestClient, db_session: Session) -> None:
    motor, _, latest = seed_api_motor(db_session)

    response = client.get(f"/api/v1/motors/{motor.id}/sensor-data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["motor_id"] == str(motor.id)
    assert payload["count"] == 2
    assert payload["items"][0]["id"] == str(latest.id)


def test_get_latest_sensor_data(client: TestClient, db_session: Session) -> None:
    motor, _, latest = seed_api_motor(db_session)

    response = client.get(f"/api/v1/motors/{motor.id}/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest"]["id"] == str(latest.id)
    assert payload["latest"]["temperature"] == "95.000"


def test_get_motor_health(client: TestClient, db_session: Session) -> None:
    motor, _, _ = seed_api_motor(db_session)

    response = client.get(f"/api/v1/motors/{motor.id}/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["health_score"] == 45
    assert payload["status"] == "Critical"
    assert set(payload.keys()) == {"health_score", "status"}


def test_missing_motor_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/motors/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
