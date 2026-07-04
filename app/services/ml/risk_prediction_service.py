import logging
from typing import List

from app.database.models.prediction_history import PredictionHistory
from app.schemas.prediction import RiskPredictionResult

logger = logging.getLogger(__name__)


class RiskPredictionService:
    """
    Computes failure probability for 7-day and 30-day horizons using:
      - Health score degradation trend (from historical predictions)
      - Current anomaly score (weighted contribution)
      - Fault classification confidence (weighted contribution)
      - Logistic mapping from projected health to failure probability
    """

    HEALTHY_THRESHOLD = 80.0
    WARNING_THRESHOLD = 60.0
    CRITICAL_THRESHOLD = 30.0

    # Feature weights
    ANOMALY_WEIGHT = 0.30
    FAULT_WEIGHT = 0.20

    def predict_risk(
        self,
        current_health: float,
        history: List[PredictionHistory],
        anomaly_score: float,
        fault_confidence: float,
        predicted_fault: str,
    ) -> RiskPredictionResult:
        degradation_rate = self._compute_degradation_rate(history)
        base_risk = self._health_to_risk(current_health)

        anomaly_contrib = anomaly_score * self.ANOMALY_WEIGHT
        fault_contrib = (
            (fault_confidence / 100.0) * self.FAULT_WEIGHT
            if predicted_fault != "Normal"
            else 0.0
        )

        risk_7d = self._project(
            base_risk, degradation_rate, 7, anomaly_contrib, fault_contrib
        )
        risk_30d = self._project(
            base_risk, degradation_rate, 30, anomaly_contrib, fault_contrib
        )

        return RiskPredictionResult(
            risk_7d=round(min(risk_7d, 1.0), 4),
            risk_30d=round(min(risk_30d, 1.0), 4),
            risk_level=self.classify_level(risk_7d, risk_30d),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_degradation_rate(
        self,
        history: List[PredictionHistory],
    ) -> float:
        """Return average health points lost per day (0 if insufficient history)."""
        if len(history) < 2:
            return 0.0

        pairs = sorted(
            [(h.prediction_date, h.health_score) for h in history],
            key=lambda x: x[0],
        )

        total_loss = 0.0
        total_days = 0.0
        for i in range(1, len(pairs)):
            elapsed = (pairs[i][0] - pairs[i - 1][0]).total_seconds() / 86_400.0
            if elapsed > 0:
                loss = pairs[i - 1][1] - pairs[i][1]  # positive = degrading
                total_loss += loss
                total_days += elapsed

        if total_days == 0.0:
            return 0.0

        # Clamp to non-negative: we only model degradation here
        return max(0.0, total_loss / total_days)

    def _health_to_risk(self, health: float) -> float:
        """Map a health score to an instantaneous failure probability."""
        if health >= self.HEALTHY_THRESHOLD:
            return 0.02
        if health >= self.WARNING_THRESHOLD:
            span = self.HEALTHY_THRESHOLD - self.WARNING_THRESHOLD
            return 0.02 + (self.HEALTHY_THRESHOLD - health) / span * 0.28
        if health >= self.CRITICAL_THRESHOLD:
            span = self.WARNING_THRESHOLD - self.CRITICAL_THRESHOLD
            return 0.30 + (self.WARNING_THRESHOLD - health) / span * 0.40
        span = self.CRITICAL_THRESHOLD
        return 0.70 + (self.CRITICAL_THRESHOLD - health) / span * 0.29

    def _project(
        self,
        base_risk: float,
        degradation_rate: float,
        horizon_days: int,
        anomaly_contrib: float,
        fault_contrib: float,
    ) -> float:
        """Project risk over a time horizon given the degradation trajectory."""
        projected_health = max(0.0, 100.0 - degradation_rate * horizon_days)
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
