"""Unit tests for FaultClassificationService."""

import pytest

from app.services.ml.fault_classification_service import (
    FAULT_CLASSES,
    FaultClassificationService,
)
from app.services.ml.feature_engineering import MotorFeatures


def _make_features(**kwargs) -> MotorFeatures:
    defaults = dict(
        temperature=65.0, vibration=3.0, current=15.0, voltage=380.0,
        power=5500.0, load=75.0, current_ratio=0.85, power_factor=0.87,
        temperature_rolling_mean=65.0, vibration_rolling_mean=3.0,
        temperature_std=2.0, vibration_std=0.3,
    )
    defaults.update(kwargs)
    return MotorFeatures(**defaults)


@pytest.fixture(scope="module")
def service() -> FaultClassificationService:
    return FaultClassificationService()


class TestFaultClassificationService:

    def test_result_has_required_fields(self, service: FaultClassificationService) -> None:
        result = service.classify(_make_features())
        assert hasattr(result, "fault")
        assert hasattr(result, "confidence")
        assert hasattr(result, "all_probabilities")

    def test_confidence_range(self, service: FaultClassificationService) -> None:
        result = service.classify(_make_features())
        assert 0.0 <= result.confidence <= 100.0

    def test_fault_is_known_class(self, service: FaultClassificationService) -> None:
        result = service.classify(_make_features())
        assert result.fault in FAULT_CLASSES

    def test_all_probabilities_sum_to_100(self, service: FaultClassificationService) -> None:
        result = service.classify(_make_features())
        total = sum(result.all_probabilities.values())
        assert abs(total - 100.0) < 0.5  # allow minor floating-point drift

    def test_overtemperature_and_voltage_instability_suggests_insulation(
        self, service: FaultClassificationService
    ) -> None:
        """Insulation Fault signature: high temp + low voltage + high current."""
        features = _make_features(
            temperature=98.0,
            voltage=345.0,
            current=21.0,
            current_ratio=1.25,
            power_factor=0.70,
            temperature_rolling_mean=94.0,
            temperature_std=5.0,
        )
        result = service.classify(features)
        # Top prediction should lean toward Insulation Fault or Rotor Fault
        assert result.fault in {"Insulation Fault", "Rotor Fault", "Overload"}

    def test_high_vibration_suggests_bearing_or_misalignment(
        self, service: FaultClassificationService
    ) -> None:
        features = _make_features(
            vibration=13.0,
            vibration_rolling_mean=12.5,
            vibration_std=2.0,
        )
        result = service.classify(features)
        assert result.fault in {"Bearing Wear", "Misalignment", "Unbalance"}

    def test_overload_signature(self, service: FaultClassificationService) -> None:
        features = _make_features(
            current=25.0,
            current_ratio=1.55,
            load=97.0,
            temperature=86.0,
            power=8700.0,
        )
        result = service.classify(features)
        assert result.fault in {"Overload", "Rotor Fault"}

    def test_normal_signature(self, service: FaultClassificationService) -> None:
        features = _make_features()
        result = service.classify(features)
        # A perfectly normal reading should have Normal as top probability
        top_fault = max(result.all_probabilities, key=result.all_probabilities.get)
        assert top_fault == "Normal"
