from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.fault_repository import FaultRepository
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.motor_repository import MotorRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.sensor_data_repository import SensorDataRepository


def create_motor(repository: MotorRepository):
    return repository.create(
        {
            "name": "Main Compressor Motor",
            "manufacturer": "WEG",
            "model": "W22",
            "rated_power_kw": Decimal("75.00"),
            "rated_voltage": Decimal("415.00"),
            "rated_current": Decimal("132.50"),
            "rpm": 1480,
            "location": "Plant 1 - Compressor Room",
            "status": "active",
        }
    )


def test_motor_repository_crud(db_session: Session) -> None:
    repository = MotorRepository(db_session)
    motor = create_motor(repository)

    assert motor.id is not None
    assert repository.get_by_id(motor.id) == motor
    assert len(repository.get_all()) == 1

    updated = repository.update(motor.id, {"status": "maintenance", "location": "Workshop"})
    assert updated is not None
    assert updated.status == "maintenance"
    assert updated.location == "Workshop"

    assert repository.delete(motor.id) is True
    assert repository.get_by_id(motor.id) is None


def test_sensor_data_repository_crud(db_session: Session) -> None:
    motor = create_motor(MotorRepository(db_session))
    repository = SensorDataRepository(db_session)

    sensor_data = repository.create(
        {
            "motor_id": motor.id,
            "temperature": Decimal("78.500"),
            "vibration": Decimal("4.200"),
            "current": Decimal("128.300"),
            "voltage": Decimal("414.800"),
            "power": Decimal("72.100"),
            "power_factor": Decimal("0.910"),
            "thd": Decimal("3.200"),
            "load": Decimal("86.000"),
            "timestamp": datetime.now(UTC),
        }
    )

    assert repository.get_by_id(sensor_data.id) == sensor_data
    assert repository.get_latest_for_motor(motor.id, limit=10)[0].id == sensor_data.id

    updated = repository.update(sensor_data.id, {"temperature": Decimal("80.000")})
    assert updated is not None
    assert updated.temperature == Decimal("80.000")

    assert repository.delete(sensor_data.id) is True


def test_fault_repository_crud(db_session: Session) -> None:
    motor = create_motor(MotorRepository(db_session))
    repository = FaultRepository(db_session)

    fault = repository.create(
        {
            "motor_id": motor.id,
            "fault_type": "Bearing Wear",
            "severity": "high",
            "confidence": Decimal("92.00"),
            "description": "Elevated vibration and temperature suggest bearing degradation.",
            "detected_at": datetime.now(UTC),
        }
    )

    assert repository.get_by_id(fault.id) == fault
    assert repository.get_for_motor(motor.id)[0].fault_type == "Bearing Wear"

    updated = repository.update(fault.id, {"severity": "critical"})
    assert updated is not None
    assert updated.severity == "critical"

    assert repository.delete(fault.id) is True


def test_maintenance_repository_crud(db_session: Session) -> None:
    motor = create_motor(MotorRepository(db_session))
    repository = MaintenanceRepository(db_session)
    performed_at = datetime.now(UTC)

    maintenance = repository.create(
        {
            "motor_id": motor.id,
            "maintenance_type": "Bearing Inspection",
            "description": "Inspected DE and NDE bearings and regreased according to procedure.",
            "performed_by": "Maintenance Team A",
            "performed_at": performed_at,
            "next_due_at": performed_at + timedelta(days=30),
        }
    )

    assert repository.get_by_id(maintenance.id) == maintenance
    assert repository.get_for_motor(motor.id)[0].maintenance_type == "Bearing Inspection"

    updated = repository.update(maintenance.id, {"performed_by": "Reliability Team"})
    assert updated is not None
    assert updated.performed_by == "Reliability Team"

    assert repository.delete(maintenance.id) is True


def test_recommendation_repository_crud(db_session: Session) -> None:
    motor = create_motor(MotorRepository(db_session))
    repository = RecommendationRepository(db_session)

    recommendation = repository.create(
        {
            "motor_id": motor.id,
            "risk_level": "high",
            "root_cause": "Likely bearing lubrication breakdown.",
            "recommended_actions": "Schedule bearing inspection and check lubrication interval.",
            "maintenance_plan": "Inspect within 7 days and trend vibration daily for 30 days.",
            "created_at": datetime.now(UTC),
        }
    )

    assert repository.get_by_id(recommendation.id) == recommendation
    assert repository.get_for_motor(motor.id)[0].risk_level == "high"

    updated = repository.update(recommendation.id, {"risk_level": "medium"})
    assert updated is not None
    assert updated.risk_level == "medium"

    assert repository.delete(recommendation.id) is True
