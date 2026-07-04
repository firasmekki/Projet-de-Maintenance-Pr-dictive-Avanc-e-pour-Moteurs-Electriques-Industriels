"""Unit tests for RiskPredictionService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.db.models.prediction_history import PredictionHistory
from app.services.ml.risk_prediction_service import RiskPredictionService


def _make_history(scores: list[float], base_date: datetime | None = None) -> list:
    base = base_date or datetime(2024, 1, 1, tzinfo=UTC)
    records = []
    for i, score in enumerate(scores):
        r = MagicMock(spec=PredictionHistory)
        r.predicted_at = base + timedelta(days=i)
        r.health_score = score
        records.append(r)
    return records


@pytest.fixture
def service() -> RiskPredictionService:
    return RiskPredictionService()


class TestRiskPredictionService:

    def test_healthy_motor_low_risk(self, service: RiskPredictionService) -> None:
        result = service.predict_risk(
            current_health=92.0, history=[],
            anomaly_score=0.05, fault_confidence=5.0, predicted_fault="Normal",
        )
        assert result.risk_7d < 0.15
        assert result.risk_30d < 0.30
        assert result.risk_level == "Low"

    def test_critical_motor_high_risk(self, service: RiskPredictionService) -> None:
        result = service.predict_risk(
            current_health=18.0, history=[],
            anomaly_score=0.92, fault_confidence=88.0, predicted_fault="Rotor Fault",
        )
        assert result.risk_7d > 0.60
        assert result.risk_level in {"High", "Critical"}

    def test_risk_scores_bounded(self, service: RiskPredictionService) -> None:
        for health in [0, 30, 60, 90]:
            result = service.predict_risk(
                current_health=float(health), history=[],
                anomaly_score=0.8, fault_confidence=80.0, predicted_fault="Overload",
            )
            assert 0.0 <= result.risk_7d <= 1.0
            assert 0.0 <= result.risk_30d <= 1.0

    def test_risk_30d_gte_risk_7d_for_degrading(self, service: RiskPredictionService) -> None:
        history = _make_history([90, 82, 74, 65, 55])
        result = service.predict_risk(
            current_health=55.0, history=history,
            anomaly_score=0.4, fault_confidence=55.0, predicted_fault="Bearing Wear",
        )
        assert result.risk_30d >= result.risk_7d

    def test_normal_fault_reduces_fault_contribution(self, service: RiskPredictionService) -> None:
        r_normal = service.predict_risk(
            current_health=85.0, history=[], anomaly_score=0.1,
            fault_confidence=90.0, predicted_fault="Normal",
        )
        r_fault = service.predict_risk(
            current_health=85.0, history=[], anomaly_score=0.1,
            fault_confidence=90.0, predicted_fault="Bearing Wear",
        )
        assert r_fault.risk_7d >= r_normal.risk_7d

    def test_degrading_history_raises_30d_risk(self, service: RiskPredictionService) -> None:
        degrading = _make_history([88, 80, 72, 63, 53, 42])
        result_with = service.predict_risk(
            current_health=42.0, history=degrading,
            anomaly_score=0.4, fault_confidence=50.0, predicted_fault="Bearing Wear",
        )
        result_without = service.predict_risk(
            current_health=42.0, history=[],
            anomaly_score=0.4, fault_confidence=50.0, predicted_fault="Bearing Wear",
        )
        assert result_with.risk_30d >= result_without.risk_30d

    def test_classify_level_thresholds(self, service: RiskPredictionService) -> None:
        assert service.classify_level(0.05, 0.10) == "Low"
        assert service.classify_level(0.25, 0.40) == "Medium"
        assert service.classify_level(0.50, 0.65) == "High"
        assert service.classify_level(0.75, 0.92) == "Critical"

    def test_risk_level_is_valid(self, service: RiskPredictionService) -> None:
        result = service.predict_risk(
            current_health=70.0, history=[],
            anomaly_score=0.3, fault_confidence=40.0, predicted_fault="Unbalance",
        )
        assert result.risk_level in {"Low", "Medium", "High", "Critical"}
