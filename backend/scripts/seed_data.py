import argparse
import math
import random
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.models.fault_history import FaultHistory
from app.db.models.maintenance_history import MaintenanceHistory
from app.db.models.motor import Motor
from app.db.models.recommendation import Recommendation
from app.db.models.sensor_data import SensorData
from app.db.session import SessionLocal

DEFAULT_MOTOR_COUNT = 10
DEFAULT_DAYS = 30
DEFAULT_READINGS_PER_DAY = 34
RANDOM_SEED = 42


MOTOR_TEMPLATES = [
    ("Compressor Drive Motor", "WEG", "W22", "Plant 1 - Compressor Room", 75, 415, 132, 1480),
    ("Cooling Tower Fan Motor", "ABB", "M3BP", "Utilities - Cooling Tower", 45, 415, 82, 1475),
    ("Main Pump Motor", "Siemens", "SIMOTICS SD", "Plant 2 - Pump Bay", 110, 415, 195, 1485),
    ("Conveyor Motor", "WEG", "W50", "Packaging Line", 30, 415, 56, 1460),
    ("Blower Motor", "ABB", "M3AA", "Furnace Area", 55, 415, 98, 1480),
    ("Hydraulic Power Unit Motor", "Siemens", "SIMOTICS GP", "Press Shop", 22, 415, 42, 1450),
    ("Crusher Motor", "WEG", "W22X", "Raw Material Handling", 160, 415, 282, 1490),
    ("Extruder Motor", "ABB", "M3GP", "Production Line 3", 90, 415, 160, 1482),
    ("Air Handling Unit Motor", "Siemens", "SIMOTICS XP", "HVAC Plant", 37, 415, 68, 1470),
    ("Boiler Feed Pump Motor", "WEG", "W22", "Boiler House", 132, 415, 232, 1488),
]


def expected_sensor_record_count(
    motor_count: int = DEFAULT_MOTOR_COUNT,
    days: int = DEFAULT_DAYS,
    readings_per_day: int = DEFAULT_READINGS_PER_DAY,
) -> int:
    return motor_count * days * readings_per_day


def _decimal(value: float, places: str = "0.001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places))


def _create_motors(motor_count: int) -> list[Motor]:
    motors: list[Motor] = []
    for index in range(motor_count):
        name, manufacturer, model, location, power_kw, voltage, current, rpm = MOTOR_TEMPLATES[
            index % len(MOTOR_TEMPLATES)
        ]
        suffix = index + 1
        motors.append(
            Motor(
                name=f"{name} {suffix:02d}",
                manufacturer=manufacturer,
                model=model,
                rated_power_kw=Decimal(power_kw),
                rated_voltage=Decimal(voltage),
                rated_current=Decimal(current),
                rpm=rpm,
                location=location,
                status="active",
            )
        )
    return motors


def _generate_sensor_records(
    motors: list[Motor],
    days: int,
    readings_per_day: int,
    rng: random.Random,
) -> list[SensorData]:
    records: list[SensorData] = []
    end_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    interval = timedelta(days=1) / readings_per_day
    total_steps = days * readings_per_day

    for motor_index, motor in enumerate(motors):
        baseline_temperature = rng.uniform(52.0, 68.0)
        baseline_vibration = rng.uniform(1.4, 3.8)
        load_bias = rng.uniform(62.0, 84.0)
        power_factor_base = rng.uniform(0.84, 0.95)
        degradation_factor = 1.0 + (motor_index / max(len(motors), 1)) * 0.18

        for step in range(total_steps):
            timestamp = end_time - (interval * (total_steps - step))
            daily_angle = (step % readings_per_day) / readings_per_day * math.tau
            weekly_angle = step / max(total_steps, 1) * math.tau * 4

            load = max(35.0, min(112.0, load_bias + 14.0 * math.sin(daily_angle) + rng.gauss(0, 4.0)))
            temperature = (
                baseline_temperature
                + (load - 70.0) * 0.22
                + 2.4 * math.sin(weekly_angle)
                + rng.gauss(0, 1.6)
            )
            vibration = baseline_vibration * degradation_factor + max(load - 85.0, 0) * 0.035 + rng.gauss(0, 0.22)
            voltage = 415.0 + rng.gauss(0, 3.2)
            current = float(motor.rated_current) * (load / 100.0) * rng.uniform(0.96, 1.06)
            power_factor = max(0.72, min(0.99, power_factor_base - max(load - 95.0, 0) * 0.001 + rng.gauss(0, 0.012)))
            power = math.sqrt(3) * voltage * current * power_factor / 1000.0
            thd = max(1.2, min(9.5, 2.4 + max(load - 85.0, 0) * 0.045 + rng.gauss(0, 0.35)))

            records.append(
                SensorData(
                    motor_id=motor.id,
                    temperature=_decimal(temperature),
                    vibration=_decimal(max(vibration, 0.2)),
                    current=_decimal(current),
                    voltage=_decimal(voltage),
                    power=_decimal(power),
                    power_factor=_decimal(power_factor),
                    thd=_decimal(thd),
                    load=_decimal(load),
                    timestamp=timestamp,
                )
            )

    return records


def reset_database(session: Session) -> None:
    session.execute(delete(SensorData))
    session.execute(delete(Recommendation))
    session.execute(delete(MaintenanceHistory))
    session.execute(delete(FaultHistory))
    session.execute(delete(Motor))
    session.commit()


def seed_database(
    session: Session,
    motor_count: int = DEFAULT_MOTOR_COUNT,
    days: int = DEFAULT_DAYS,
    readings_per_day: int = DEFAULT_READINGS_PER_DAY,
    reset: bool = False,
) -> dict[str, Any]:
    if reset:
        reset_database(session)

    existing_motors = session.scalar(select(func.count(Motor.id))) or 0
    existing_sensor_records = session.scalar(select(func.count(SensorData.id))) or 0
    target_sensor_records = expected_sensor_record_count(motor_count, days, readings_per_day)

    if existing_motors >= motor_count and existing_sensor_records >= target_sensor_records:
        return {
            "created_motors": 0,
            "created_sensor_records": 0,
            "total_motors": int(existing_motors),
            "total_sensor_records": int(existing_sensor_records),
            "skipped": True,
        }

    rng = random.Random(RANDOM_SEED)
    motors = _create_motors(motor_count)
    session.add_all(motors)
    session.commit()

    for motor in motors:
        session.refresh(motor)

    sensor_records = _generate_sensor_records(motors, days, readings_per_day, rng)
    session.add_all(sensor_records)
    session.commit()

    return {
        "created_motors": len(motors),
        "created_sensor_records": len(sensor_records),
        "total_motors": int(session.scalar(select(func.count(Motor.id))) or 0),
        "total_sensor_records": int(session.scalar(select(func.count(SensorData.id))) or 0),
        "skipped": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed ORBIT AI motor and sensor data.")
    parser.add_argument("--motors", type=int, default=DEFAULT_MOTOR_COUNT)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--readings-per-day", type=int, default=DEFAULT_READINGS_PER_DAY)
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with SessionLocal() as session:
        result = seed_database(
            session=session,
            motor_count=args.motors,
            days=args.days,
            readings_per_day=args.readings_per_day,
            reset=args.reset,
        )

    print(
        "Seed complete: "
        f"{result['created_motors']} motors, "
        f"{result['created_sensor_records']} sensor records created. "
        f"Totals: {result['total_motors']} motors, "
        f"{result['total_sensor_records']} sensor records."
    )


if __name__ == "__main__":
    main()
