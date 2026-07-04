"""Unit tests for PredictionService (mocked dependencies)."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.database.models.motor import Motor
from app.database.models.sensor_data import SensorData
from app.schemas.prediction import (
    AnomalyResult,
    FaultClassificationResult,
    HealthPredictionResult,
)
from app.services.ml.feature_engineering import MotorFeatures
from app.services.ml.prediction_service import PredictionService


def _make_motor(rated_current: float = 18.0, rated_voltage: float = 380.0) -> Motor:
    m = MagicMock(spec=Motor)
    m.id = uuid4()
    m.rated_current = rated_current
    m.rated_voltage = rated_voltage
    return m


def _make_sensor() -> SensorData:
    s = MagicMock(spec=SensorData)
    s.temperature = 70.0
    s.vibration = 3.5
    s.current = 16.0
    s.voltage = 381.0
    s.power = 5800.0
    s.load_percentage = 78.0
    s.recorded_at = datetime.utcnow()
    return s


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(session: AsyncMock) -> PredictionService:
    return PredictionService(session)


class TestPredictionService:

    @pytest.mark.asyncio
    async def test_predict_returns_response(self, service: PredictionService) -> None:
        motor = _make_motor()
        sensors = [_make_sensor() for _ in range(5)]
        motor_id = motor.id

        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=sensors)
        service._prediction_repo.get_risk_history = AsyncMock(return_value=[])
        service._prediction_repo.create = AsyncMock()

        result = await service.predict(motor_id)

        assert result.motor_id == motor_id
        assert result.model_version == "1.0.0"
        assert 0.0 <= result.health.health_score <= 100.0
        assert result.health.status in {"Healthy", "Warning", "Critical"}
        assert 0.0 <= result.anomaly.score <= 1.0
        assert result.fault_classification.fault is not None
        assert 0.0 <= result.risk.risk_7d <= 1.0
        assert 0.0 <= result.risk.risk_30d <= 1.0

    @pytest.mark.asyncio
    async def test_predict_raises_if_motor_not_found(self, service: PredictionService) -> None:
        service._motor_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await service.predict(uuid4())

    @pytest.mark.asyncio
    async def test_predict_raises_if_no_sensor_data(self, service: PredictionService) -> None:
        service._motor_repo.get_by_id = AsyncMock(return_value=_make_motor())
        service._sensor_repo.get_recent = AsyncMock(return_value=[])

        with pytest.raises(ValueError, match="No sensor data"):
            await service.predict(uuid4())

    @pytest.mark.asyncio
    async def test_predict_persists_record(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=[_make_sensor()])
        service._prediction_repo.get_risk_history = AsyncMock(return_value=[])
        service._prediction_repo.create = AsyncMock()

        await service.predict(motor.id)

        service._prediction_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_with_features_returns_features(self, service: PredictionService) -> None:
        motor = _make_motor()
        service._motor_repo.get_by_id = AsyncMock(return_value=motor)
        service._sensor_repo.get_recent = AsyncMock(return_value=[_make_sensor()])
        service._prediction_repo.get_risk_history = AsyncMock(return_value=[])
        service._prediction_repo.create = AsyncMock()

        result = await service.predict(motor.id, include_features=True)

        assert result.features is not None
        assert "temperature" in result.features
        assert "vibration" in result.features

    def test_compute_health_healthy(self, service: PredictionService) -> None:
        features = MotorFeatures(
            temperature=65, vibration=3, current=15, voltage=380, power=5500, load=75,
            current_ratio=0.85, power_factor=0.87,
            temperature_rolling_mean=65, vibration_rolling_mean=3,
            temperature_std=2, vibration_std=0.3,
        )
        anomaly = AnomalyResult(anomaly=False, score=0.05)
        fault = FaultClassificationResult(fault="Normal", confidence=90.0, all_probabilities={})

        result = service._compute_health(features, anomaly, fault)

        assert result.status == "Healthy"
        assert result.health_score >= 75.0

    def test_compute_health_critical(self, service: PredictionService) -> None:
        features = MotorFeatures(
            temperature=100, vibration=12, current=25, voltage=350, power=8500, load=98,
            current_ratio=1.6, power_factor=0.70,
            temperature_rolling_mean=98, vibration_rolling_mean=11,
            temperature_std=6, vibration_std=2,
        )
        anomaly = AnomalyResult(anomaly=True, score=0.92)
        fault = FaultClassificationResult(fault="Overload", confidence=88.0, all_probabilities={})

        result = service._compute_health(features, anomaly, fault)

        assert result.status in {"Warning", "Critical"}
        assert result.health_score < 75.0

    @pytest.mark.asyncio
    async def test_get_risk_motor_not_found(self, service: PredictionService) -> None:
        service._motor_repo.exists = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="not found"):
            await service.get_risk(uuid4())

    @pytest.mark.asyncio
    async def test_get_risk_no_predictions(self, service: PredictionService) -> None:
        service._motor_repo.exists = AsyncMock(return_value=True)
        service._prediction_repo.get_latest_by_motor_id = AsyncMock(return_value=None)
        service._prediction_repo.get_risk_history = AsyncMock(return_value=[])

        motor_id = uuid4()
        result = await service.get_risk(motor_id)

        assert result.motor_id == motor_id
        assert result.current_health_score == 100.0
        assert result.risk_level == "Low"
        assert result.last_prediction is None
