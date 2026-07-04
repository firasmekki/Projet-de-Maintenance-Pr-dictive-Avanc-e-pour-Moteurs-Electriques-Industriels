"""Unit tests for AnomalyDetectionService."""

import numpy as np
import pytest

from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.feature_engineering import MotorFeatures


def _normal_features(**overrides) -> MotorFeatures:
    defaults = dict(
        temperature=65.0, vibration=3.0, current=15.0, voltage=380.0,
        power=5500.0, load=75.0, power_factor=0.87, thd=3.5,
        current_ratio=0.85, temperature_mean=65.0, vibration_mean=3.0,
        temperature_std=2.0, vibration_std=0.3,
    )
    defaults.update(overrides)
    return MotorFeatures(**defaults)


@pytest.fixture(scope="module")
def service() -> AnomalyDetectionService:
    return AnomalyDetectionService()


class TestAnomalyDetectionService:

    def test_result_has_required_fields(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features())
        assert hasattr(result, "anomaly")
        assert hasattr(result, "score")

    def test_score_is_in_range(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features())
        assert 0.0 <= result.score <= 1.0

    def test_anomaly_is_bool(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features())
        assert isinstance(result.anomaly, bool)

    def test_normal_readings_produce_low_score(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features())
        # Perfectly normal input should score below 0.6
        assert result.score < 0.6

    def test_extreme_temperature_raises_score(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features(temperature=135.0, temperature_mean=133.0))
        # Severe anomaly should raise the score
        assert result.score > 0.4

    def test_extreme_vibration_raises_score(self, service: AnomalyDetectionService) -> None:
        result = service.detect(_normal_features(vibration=20.0, vibration_mean=19.5))
        assert result.score > 0.4

    def test_score_monotone_with_anomaly_severity(self, service: AnomalyDetectionService) -> None:
        s_low = service.detect(_normal_features(temperature=75.0)).score
        s_high = service.detect(_normal_features(temperature=130.0)).score
        assert s_high >= s_low

    def test_all_temperatures_produce_bounded_score(self, service: AnomalyDetectionService) -> None:
        for temp in [40, 65, 90, 115, 140]:
            result = service.detect(_normal_features(temperature=float(temp)))
            assert 0.0 <= result.score <= 1.0

    def test_retrain_does_not_raise(self, service: AnomalyDetectionService, tmp_path, monkeypatch) -> None:
        import app.services.ml.anomaly_detection_service as mod
        monkeypatch.setattr(mod, "_MODEL_DIR", tmp_path)
        monkeypatch.setattr(mod, "_MODEL_PATH", tmp_path / "anomaly_detector.pkl")

        fresh = AnomalyDetectionService()
        X = np.random.default_rng(0).normal(0, 1, (300, 13)).astype(np.float32)
        fresh.retrain(X)  # should not raise
