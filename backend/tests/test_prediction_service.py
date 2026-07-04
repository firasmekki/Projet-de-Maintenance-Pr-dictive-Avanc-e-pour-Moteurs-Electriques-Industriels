"""
Unit tests for PredictionService.
All repositories are mocked — no database required.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.db.models.motor import Motor
from app.db.models.prediction_history import PredictionHistory
from app.db.models.sensor_data import SensorData
from app.repositories.motor_repository import MotorRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.sensor_data_repository import SensorDataRepository
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.fault_classification_service import FaultClassificationService
from app.services.ml.feature_engineering import FeatureEngineer
from app.services.ml.prediction_service import PredictionService
from app.services.ml.risk_prediction_service import RiskPredictionService


def _mock_motor(rated_current: float = 18.0, rated_voltage: float = 380.0) -> Motor:
    m = MagicMock(spec=Motor)
    m.id = uuid4()
    m.rated_current = Decimal(str(rated_current))
    m.rated_voltage = Decimal(str(rated_voltage))
    return m


def _mock_sensor(
    temperature: float = 70.0,
    vibration: float = 3.5,
    current: float = 15.5,
    voltage: float = 380.0,
    power: float = 5600.0,
    load: float = 77.0,
    power_factor: float = 0.87,
    thd: float = 3.5,
) -> SensorData:
    s = MagicMock(spec=SensorData)
    s.temperature = Decimal(str(temperature))
    s.vibration = Decimal(str(vibration))
    s.current = Decimal(str(current))
    s.voltage = Decimal(str(voltage))
    s.power = Decimal(str(power))
    s.load = Decimal(str(load))
    s.power_factor = Decimal(str(power_factor))
    s.thd = Decimal(str(thd))
    s.timestamp = datetime.now(UTC)
    return s


def _make_service() -> PredictionService:
    return PredictionService(
        motor_repo=MagicMock(spec=MotorRepository),
        sensor_repo=MagicMock(spec=SensorDataRepository),
        prediction_repo=MagicMock(spec=PredictionRepository),
        anomaly_svc=AnomalyDetectionService(),
        fault_svc=FaultClassificationService(),
        risk_svc=RiskPredictionService(),
        feature_engineer=FeatureEngineer(),
    )


class TestPredictionServicePredict:

    def test_returns_none_when_motor_not_found(self) -> None:
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = None
        assert svc.predict(uuid4()) is None

    def test_returns_none_when_no_sensor_data(self) -> None:
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = _mock_motor()
        svc._sensor_repo.get_latest_for_motor.return_value = []
        assert svc.predict(uuid4()) is None

    def test_returns_prediction_response(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._sensor_repo.get_latest_for_motor.return_value = [_mock_sensor() for _ in range(5)]
        svc._prediction_repo.get_risk_history.return_value = []
        svc._prediction_repo.create.return_value = MagicMock(
            id=uuid4(), predicted_at=datetime.now(UTC)
        )

        result = svc.predict(motor.id)

        assert result is not None
        assert result.motor_id == motor.id
        assert result.model_version == "1.0.0"
        assert 0.0 <= result.health.health_score <= 100.0
        assert result.health.status in {"Healthy", "Warning", "Critical"}
        assert 0.0 <= result.anomaly.score <= 1.0
        assert result.fault_classification.fault is not None
        assert 0.0 <= result.risk.risk_7d <= 1.0
        assert 0.0 <= result.risk.risk_30d <= 1.0

    def test_persists_record(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._sensor_repo.get_latest_for_motor.return_value = [_mock_sensor()]
        svc._prediction_repo.get_risk_history.return_value = []
        svc._prediction_repo.create.return_value = MagicMock(
            id=uuid4(), predicted_at=datetime.now(UTC)
        )

        svc.predict(motor.id)

        svc._prediction_repo.create.assert_called_once()
        payload = svc._prediction_repo.create.call_args[0][0]
        assert payload["motor_id"] == motor.id
        assert "health_score" in payload
        assert "risk_score_7d" in payload
        assert "anomaly_detected" in payload

    def test_include_features_populates_features(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._sensor_repo.get_latest_for_motor.return_value = [_mock_sensor()]
        svc._prediction_repo.get_risk_history.return_value = []
        svc._prediction_repo.create.return_value = MagicMock(
            id=uuid4(), predicted_at=datetime.now(UTC)
        )

        result = svc.predict(motor.id, include_features=True)

        assert result is not None
        assert result.features is not None
        assert "temperature" in result.features
        assert "vibration" in result.features

    def test_no_features_by_default(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._sensor_repo.get_latest_for_motor.return_value = [_mock_sensor()]
        svc._prediction_repo.get_risk_history.return_value = []
        svc._prediction_repo.create.return_value = MagicMock(
            id=uuid4(), predicted_at=datetime.now(UTC)
        )

        result = svc.predict(motor.id)

        assert result is not None
        assert result.features is None


class TestPredictionServiceGetPredictions:

    def test_returns_none_when_motor_not_found(self) -> None:
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = None
        assert svc.get_predictions(uuid4()) is None

    def test_returns_list_response(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._prediction_repo.get_by_motor_id.return_value = []
        svc._prediction_repo.count_by_motor_id.return_value = 0

        result = svc.get_predictions(motor.id)

        assert result is not None
        assert result.motor_id == motor.id
        assert result.total == 0
        assert result.items == []


class TestPredictionServiceGetRisk:

    def test_returns_none_when_motor_not_found(self) -> None:
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = None
        assert svc.get_risk(uuid4()) is None

    def test_returns_default_when_no_predictions(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor
        svc._prediction_repo.get_latest_by_motor_id.return_value = None
        svc._prediction_repo.get_risk_history.return_value = []

        result = svc.get_risk(motor.id)

        assert result is not None
        assert result.current_health_score == 100.0
        assert result.risk_level == "Low"
        assert result.last_predicted_at is None
        assert len(result.recommendations) == 1

    def test_recommendations_include_anomaly_warning(self) -> None:
        motor = _mock_motor()
        svc = _make_service()
        svc._motor_repo.get_by_id.return_value = motor

        latest = MagicMock(spec=PredictionHistory)
        latest.anomaly_detected = True
        latest.predicted_fault = "Bearing Wear"
        latest.health_score = Decimal("45.00")
        latest.risk_score_7d = Decimal("0.7500")
        latest.risk_score_30d = Decimal("0.8800")
        latest.predicted_at = datetime.now(UTC)

        svc._prediction_repo.get_latest_by_motor_id.return_value = latest
        svc._prediction_repo.get_risk_history.return_value = [latest]

        result = svc.get_risk(motor.id)

        assert any("Anomaly" in r for r in result.recommendations)
        assert any("Bearing Wear" in r for r in result.recommendations)


class TestComputeHealth:

    def _service(self) -> PredictionService:
        return _make_service()

    def test_healthy_inputs_produce_healthy_status(self) -> None:
        from app.schemas.prediction import AnomalyResult, FaultClassificationResult
        from app.services.ml.feature_engineering import MotorFeatures

        features = MotorFeatures(
            temperature=65, vibration=3, current=15, voltage=380, power=5500,
            load=75, power_factor=0.87, thd=3.5, current_ratio=0.85,
            temperature_mean=65, vibration_mean=3, temperature_std=2, vibration_std=0.3,
        )
        anomaly = AnomalyResult(anomaly=False, score=0.05)
        fault = FaultClassificationResult(fault="Normal", confidence=90.0, all_probabilities={})

        result = PredictionService._compute_health(features, anomaly, fault)

        assert result.status == "Healthy"
        assert result.health_score >= 75.0

    def test_critical_inputs_produce_critical_or_warning_status(self) -> None:
        from app.schemas.prediction import AnomalyResult, FaultClassificationResult
        from app.services.ml.feature_engineering import MotorFeatures

        features = MotorFeatures(
            temperature=100, vibration=12, current=26, voltage=350, power=9000,
            load=98, power_factor=0.70, thd=7.0, current_ratio=1.6,
            temperature_mean=98, vibration_mean=11, temperature_std=6, vibration_std=2,
        )
        anomaly = AnomalyResult(anomaly=True, score=0.92)
        fault = FaultClassificationResult(fault="Overload", confidence=89.0, all_probabilities={})

        result = PredictionService._compute_health(features, anomaly, fault)

        assert result.status in {"Warning", "Critical"}
        assert result.health_score < 75.0
