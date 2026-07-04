from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.motor import Motor
from app.db.models.sensor_data import SensorData
from scripts.seed_data import expected_sensor_record_count, seed_database


def test_expected_sensor_record_count_default_is_at_least_10000() -> None:
    assert expected_sensor_record_count() == 10200


def test_seed_database_creates_motors_and_sensor_records(db_session: Session) -> None:
    result = seed_database(
        db_session,
        motor_count=2,
        days=2,
        readings_per_day=3,
        reset=True,
    )

    assert result["created_motors"] == 2
    assert result["created_sensor_records"] == 12
    assert db_session.scalar(select(func.count(Motor.id))) == 2
    assert db_session.scalar(select(func.count(SensorData.id))) == 12
