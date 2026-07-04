"""Unit tests for FaultClassificationService."""

import pytest

from app.services.ml.fault_classification_service import (
    FAULT_CLASSES,
    FaultClassificationService,
)
from app.services.ml.feature_engineering import MotorFeatures


def _features(**overrides) -> MotorFeatures:
    defaults = dict(
        temperature=65.0, vibration=3.0, current=15.0, voltage=380.0,
        power=5500.0, load=75.0, power_factor=0.87, thd=3.5,
        current_ratio=0.85, temperature_mean=65.0, vibration_mean=3.0,
        temperature_std=2.0, vibration_std=0.3,
    )
    defaults.update(overrides)
    return MotorFeatures(**defaults)


@pytest.fixture(scope="module")
def service() -> FaultClassificationService:
    return FaultClassificationService()


class TestFaultClassificationService:

    def test_result_has_required_fields(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        assert hasattr(result, "fault")
        assert hasattr(result, "confidence")
        assert hasattr(result, "all_probabilities")

    def test_confidence_range(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        assert 0.0 <= result.confidence <= 100.0

    def test_fault_is_known_class(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        assert result.fault in FAULT_CLASSES

    def test_all_probabilities_keys_are_fault_classes(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        for key in result.all_probabilities:
            assert key in FAULT_CLASSES

    def test_all_probabilities_sum_to_100(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        total = sum(result.all_probabilities.values())
        assert abs(total - 100.0) < 1.0

    def test_normal_signature_predicts_normal(self, service: FaultClassificationService) -> None:
        result = service.classify(_features())
        top = max(result.all_probabilities, key=result.all_probabilities.get)
        assert top == "Normal"

    def test_high_vibration_suggests_bearing_or_misalignment(
        self, service: FaultClassificationService
    ) -> None:
        result = service.classify(_features(
            vibration=13.0, vibration_mean=12.5, vibration_std=2.0
        ))
        assert result.fault in {"Bearing Wear", "Misalignment", "Unbalance"}

    def test_high_current_suggests_rotor_or_overload(
        self, service: FaultClassificationService
    ) -> None:
        result = service.classify(_features(
            current=24.0, current_ratio=1.5, load=96.0,
            temperature=86.0, power=8700.0
        ))
        assert result.fault in {"Overload", "Rotor Fault"}

    def test_insulation_fault_signature(self, service: FaultClassificationService) -> None:
        result = service.classify(_features(
            temperature=97.0, voltage=348.0, current=20.5,
            current_ratio=1.22, power_factor=0.70,
            thd=6.5, temperature_mean=93.0, temperature_std=5.0
        ))
        # Should lean toward insulation or rotor fault
        assert result.fault in {"Insulation Fault", "Rotor Fault", "Overload"}

    def test_winning_probability_equals_confidence(
        self, service: FaultClassificationService
    ) -> None:
        result = service.classify(_features())
        winning_prob = result.all_probabilities[result.fault]
        assert abs(winning_prob - result.confidence) < 0.1
