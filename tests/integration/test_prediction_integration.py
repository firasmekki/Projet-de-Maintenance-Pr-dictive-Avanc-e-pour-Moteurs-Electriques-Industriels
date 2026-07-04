"""
Integration tests for the prediction pipeline.

These tests run the full ML stack end-to-end against real sklearn models
but use mocked repositories to avoid a live database.

Run with:
    pytest tests/integration/ -v
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.database.models.motor import Motor
from app.database.models.sensor_data import SensorData
from app.services.ml.prediction_service import PredictionService


def _make_motor(rated_current=18.0, rated_voltage=380.0) -> Motor:
    m = MagicMock(spec=Motor)
    m.id = uuid4()
    m.rated_current = rated_current
    m.rated_voltage = rated_voltage
    return m


def _make_sensor_batch(
    n: int = 10,
    temperature: float = 65.0,
    vibration: float = 3.0,
    current: float = 15.0,
    voltage: float = 380.0,
    power: float = 5500.0,
    load: float = 75.0,
) -> list:
    sensors = []
    for _ in range(n):
        s = MagicMock(spec=SensorData)
        s.temperature = temperature
        s.vibration = vibration
        s.current = current
        s.voltage = voltage
        s.power = power
        s.load_percentage = load
        s.recorded_at = datetime.utcnow()
        sensors.append(s)
    return sensors


@pytest.fixture
def service() -> PredictionService:
    svc = PredictionService(AsyncMock())
    svc._prediction_repo.create = AsyncMock()
    svc._prediction_repo.get_risk_history = AsyncMock(return_value=[])
    return svc


class TestPredictionPipelineIntegration:

    @pytest.mark.asyncio
    async def test_healthy_motor_full_pipeline(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(
            return_value=_make_sensor_batch(temperature=65, vibration=2.5, current=14.0)
        )

        result = await service.predict(motor.id)

        assert result.health.status in {"Healthy", "Warning"}
        assert result.anomaly.score < 0.7
        assert result.risk.risk_level in {"Low", "Medium"}
        assert result.fault_classification.fault in {"Normal", "Unbalance", "Bearing Wear"}

    @pytest.mark.asyncio
    async def test_overload_motor_full_pipeline(self, service: PredictionService) -> None:
        motor = _make_motor(rated_current=18.0)
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(
            return_value=_make_sensor_batch(
                temperature=87.0,
                vibration=5.5,
                current=27.0,
                load=97.0,
                power=9000.0,
            )
        )

        result = await service.predict(motor.id)

        assert result.health.status in {"Warning", "Critical"}
        assert result.health.health_score < 80.0
        assert result.fault_classification.fault in {
            "Overload", "Rotor Fault", "Insulation Fault"
        }

    @pytest.mark.asyncio
    async def test_bearing_wear_signature(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        sensors = _make_sensor_batch(
            n=15,
            vibration=10.5,
            temperature=79.0,
            current=15.5,
        )
        service._sensor_repo.get_recent = AsyncMock(return_value=sensors)

        result = await service.predict(motor.id)

        # High vibration should be captured
        assert result.fault_classification.fault in {
            "Bearing Wear", "Misalignment", "Unbalance"
        }

    @pytest.mark.asyncio
    async def test_insulation_fault_signature(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        sensors = _make_sensor_batch(
            temperature=97.0,
            voltage=348.0,
            current=21.0,
            power=7000.0,
        )
        service._sensor_repo.get_recent = AsyncMock(return_value=sensors)

        result = await service.predict(motor.id)

        assert result.health.health_score < 85.0

    @pytest.mark.asyncio
    async def test_pipeline_result_persisted(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=_make_sensor_batch())

        await service.predict(motor.id)

        service._prediction_repo.create.assert_called_once()
        saved = service._prediction_repo.create.call_args[0][0]
        assert saved.motor_id == motor.id
        assert saved.model_version == "1.0.0"
        assert saved.health_score is not None
        assert saved.health_status in {"Healthy", "Warning", "Critical"}

    @pytest.mark.asyncio
    async def test_risk_output_schema(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=_make_sensor_batch())

        result = await service.predict(motor.id)

        assert hasattr(result.risk, "risk_7d")
        assert hasattr(result.risk, "risk_30d")
        assert hasattr(result.risk, "risk_level")
        assert result.risk.risk_level in {"Low", "Medium", "High", "Critical"}
        assert 0.0 <= result.risk.risk_7d <= 1.0
        assert 0.0 <= result.risk.risk_30d <= 1.0

    @pytest.mark.asyncio
    async def test_anomaly_output_schema(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=_make_sensor_batch())

        result = await service.predict(motor.id)

        assert isinstance(result.anomaly.anomaly, bool)
        assert 0.0 <= result.anomaly.score <= 1.0
