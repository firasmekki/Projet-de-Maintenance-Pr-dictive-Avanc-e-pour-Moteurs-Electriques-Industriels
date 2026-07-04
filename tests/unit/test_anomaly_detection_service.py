"""Unit tests for AnomalyDetectionService."""

import numpy as np
import pytest

from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.feature_engineering import MotorFeatures


def _make_features(
    temperature: float = 65.0,
    vibration: float = 3.0,
    current: float = 15.0,
    voltage: float = 380.0,
    power: float = 5500.0,
    load: float = 75.0,
    current_ratio: float = 0.85,
    power_factor: float = 0.87,
    temp_mean: float = 65.0,
    vib_mean: float = 3.0,
    temp_std: float = 2.0,
    vib_std: float = 0.3,
) -> MotorFeatures:
    return MotorFeatures(
        temperature=temperature,
        vibration=vibration,
        current=current,
        voltage=voltage,
        power=power,
        load=load,
        current_ratio=current_ratio,
        power_factor=power_factor,
        temperature_rolling_mean=temp_mean,
        vibration_rolling_mean=vib_mean,
        temperature_std=temp_std,
        vibration_std=vib_std,
    )


@pytest.fixture(scope="module")
def service() -> AnomalyDetectionService:
    return AnomalyDetectionService()


class TestAnomalyDetectionService:

    def test_normal_operation_not_anomaly(self, service: AnomalyDetectionService) -> None:
        features = _make_features()
        result = service.detect(features)
        assert isinstance(result.anomaly, bool)
        assert 0.0 <= result.score <= 1.0
        # Normal readings should yield a low anomaly score
        assert result.score < 0.6

    def test_overtemperature_flags_as_anomaly(self, service: AnomalyDetectionService) -> None:
        features = _make_features(temperature=130.0, temp_mean=128.0, temp_std=5.0)
        result = service.detect(features)
        # High temperature well above normal range should produce a high score
        assert result.score > 0.4

    def test_high_vibration_flags_as_anomaly(self, service: AnomalyDetectionService) -> None:
        features = _make_features(vibration=18.0, vib_mean=17.5, vib_std=2.0)
        result = service.detect(features)
        assert result.score > 0.4

    def test_score_is_normalised(self, service: AnomalyDetectionService) -> None:
        for temp in [50, 70, 90, 120]:
            features = _make_features(temperature=float(temp))
            result = service.detect(features)
            assert 0.0 <= result.score <= 1.0

    def test_result_structure(self, service: AnomalyDetectionService) -> None:
        features = _make_features()
        result = service.detect(features)
        assert hasattr(result, "anomaly")
        assert hasattr(result, "score")

    def test_retrain_with_array(self, service: AnomalyDetectionService, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))
        import app.services.ml.anomaly_detection_service as mod
        monkeypatch.setattr(mod, "MODEL_PATH", str(tmp_path / "anomaly_detector.pkl"))
        monkeypatch.setattr(mod, "MODEL_DIR", str(tmp_path))

        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (500, 12)).astype(np.float32)
        fresh = AnomalyDetectionService()
        fresh.retrain(X)  # should not raise
