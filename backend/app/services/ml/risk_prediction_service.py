import logging
from collections.abc import Sequence

from app.db.models.prediction_history import PredictionHistory
from app.schemas.prediction import RiskPredictionResult

logger = logging.getLogger(__name__)


class RiskPredictionService:
    """
    Failure probability estimator for 7-day and 30-day horizons.

    Approach:
    1. Compute instantaneous base risk from current health score (logistic mapping).
    2. Estimate health degradation rate from recent prediction history (points/day).
    3. Project base risk forward using degradation trajectory.
    4. Add anomaly and fault contributions as independent risk factors.
    """

    _HEALTHY_THRESHOLD = 80.0
    _WARNING_THRESHOLD = 60.0
    _CRITICAL_THRESHOLD = 30.0

    _ANOMALY_WEIGHT = 0.30
    _FAULT_WEIGHT = 0.20

    def predict_risk(
        self,
        current_health: float,
        history: Sequence[PredictionHistory],
        anomaly_score: float,
        fault_confidence: float,
        predicted_fault: str,
    ) -> RiskPredictionResult:
        degradation_rate = self._compute_degradation_rate(history)
        base_risk = self._health_to_risk(current_health)

        anomaly_contrib = anomaly_score * self._ANOMALY_WEIGHT
        fault_contrib = (
            (fault_confidence / 100.0) * self._FAULT_WEIGHT
            if predicted_fault != "Normal"
            else 0.0
        )

        risk_7d = self._project(current_health, degradation_rate, 7, anomaly_contrib, fault_contrib)
        risk_30d = self._project(current_health, degradation_rate, 30, anomaly_contrib, fault_contrib)

        return RiskPredictionResult(
            risk_7d=round(min(risk_7d, 1.0), 4),
            risk_30d=round(min(risk_30d, 1.0), 4),
            risk_level=self.classify_level(risk_7d, risk_30d),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_degradation_rate(self, history: Sequence[PredictionHistory]) -> float:
        """Return average health-score points lost per day (≥ 0)."""
        if len(history) < 2:
            return 0.0

        pairs = sorted(
            [(h.predicted_at, float(h.health_score)) for h in history],
            key=lambda x: x[0],
        )

        total_loss, total_days = 0.0, 0.0
        for i in range(1, len(pairs)):
            elapsed = (pairs[i][0] - pairs[i - 1][0]).total_seconds() / 86_400.0
            if elapsed > 0:
                loss = pairs[i - 1][1] - pairs[i][1]
                total_loss += loss
                total_days += elapsed

        return max(0.0, total_loss / total_days) if total_days > 0 else 0.0

    def _health_to_risk(self, health: float) -> float:
        """Map current health score to an instantaneous failure probability."""
        if health >= self._HEALTHY_THRESHOLD:
            return 0.02
        if health >= self._WARNING_THRESHOLD:
            span = self._HEALTHY_THRESHOLD - self._WARNING_THRESHOLD
            return 0.02 + (self._HEALTHY_THRESHOLD - health) / span * 0.28
        if health >= self._CRITICAL_THRESHOLD:
            span = self._WARNING_THRESHOLD - self._CRITICAL_THRESHOLD
            return 0.30 + (self._WARNING_THRESHOLD - health) / span * 0.40
        span = self._CRITICAL_THRESHOLD
        return 0.70 + (self._CRITICAL_THRESHOLD - health) / span * 0.29

    def _project(
        self,
        current_health: float,
        degradation_rate: float,
        horizon_days: int,
        anomaly_contrib: float,
        fault_contrib: float,
    ) -> float:
        """Project health forward by horizon_days, then map to risk probability."""
        projected_health = max(0.0, current_health - degradation_rate * horizon_days)
        projected_risk = self._health_to_risk(projected_health)
        return min(projected_risk + anomaly_contrib + fault_contrib, 1.0)

    def classify_level(self, risk_7d: float, risk_30d: float) -> str:
        if risk_7d >= 0.70 or risk_30d >= 0.90:
            return "Critical"
        if risk_7d >= 0.40 or risk_30d >= 0.60:
            return "High"
        if risk_7d >= 0.20 or risk_30d >= 0.35:
            return "Medium"
        return "Low"
