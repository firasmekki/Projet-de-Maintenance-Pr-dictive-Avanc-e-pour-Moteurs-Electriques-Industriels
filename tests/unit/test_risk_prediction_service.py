"""Unit tests for RiskPredictionService."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.database.models.prediction_history import PredictionHistory
from app.services.ml.risk_prediction_service import RiskPredictionService


def _make_history(health_scores, base_date=None) -> list:
    base = base_date or datetime(2024, 1, 1)
    records = []
    for i, score in enumerate(health_scores):
        r = MagicMock(spec=PredictionHistory)
        r.prediction_date = base + timedelta(days=i)
        r.health_score = score
        records.append(r)
    return records


@pytest.fixture
def service() -> RiskPredictionService:
    return RiskPredictionService()


class TestRiskPredictionService:

    def test_healthy_motor_low_risk(self, service: RiskPredictionService) -> None:
        result = service.predict_risk(
            current_health=90.0,
            history=[],
            anomaly_score=0.05,
            fault_confidence=10.0,
            predicted_fault="Normal",
        )
        assert result.risk_7d < 0.20
        assert result.risk_30d < 0.35
        assert result.risk_level == "Low"

    def test_critical_motor_high_risk(self, service: RiskPredictionService) -> None:
        result = service.predict_risk(
            current_health=20.0,
            history=[],
            anomaly_score=0.90,
            fault_confidence=85.0,
            predicted_fault="Rotor Fault",
        )
        assert result.risk_7d > 0.60
        assert result.risk_level in {"High", "Critical"}

    def test_degrading_history_increases_30d_risk(self, service: RiskPredictionService) -> None:
        degrading = _make_history([95, 90, 84, 77, 69, 60, 50, 40])
        result_with_history = service.predict_risk(
            current_health=40.0,
            history=degrading,
            anomaly_score=0.50,
            fault_confidence=60.0,
            predicted_fault="Bearing Wear",
        )
        result_no_history = service.predict_risk(
            current_health=40.0,
            history=[],
            anomaly_score=0.50,
            fault_confidence=60.0,
            predicted_fault="Bearing Wear",
        )
        assert result_with_history.risk_30d >= result_no_history.risk_30d

    def test_normal_fault_zero_fault_contribution(self, service: RiskPredictionService) -> None:
        r1 = service.predict_risk(
            current_health=85.0, history=[], anomaly_score=0.1,
            fault_confidence=80.0, predicted_fault="Normal",
        )
        r2 = service.predict_risk(
            current_health=85.0, history=[], anomaly_score=0.1,
            fault_confidence=80.0, predicted_fault="Bearing Wear",
        )
        # Fault contribution should make r2 riskier
        assert r2.risk_7d >= r1.risk_7d

    def test_risk_scores_bounded(self, service: RiskPredictionService) -> None:
        for health in [0, 25, 50, 75, 100]:
            result = service.predict_risk(
                current_health=float(health),
                history=[],
                anomaly_score=0.8,
                fault_confidence=90.0,
                predicted_fault="Overload",
            )
            assert 0.0 <= result.risk_7d <= 1.0
            assert 0.0 <= result.risk_30d <= 1.0

    def test_risk_7d_leq_risk_30d_for_degrading(self, service: RiskPredictionService) -> None:
        history = _make_history([80, 70, 60, 50])
        result = service.predict_risk(
            current_health=50.0,
            history=history,
            anomaly_score=0.4,
            fault_confidence=50.0,
            predicted_fault="Bearing Wear",
        )
        assert result.risk_30d >= result.risk_7d

    def test_classify_level_thresholds(self, service: RiskPredictionService) -> None:
        assert service.classify_level(0.05, 0.10) == "Low"
        assert service.classify_level(0.25, 0.40) == "Medium"
        assert service.classify_level(0.50, 0.65) == "High"
        assert service.classify_level(0.75, 0.92) == "Critical"
