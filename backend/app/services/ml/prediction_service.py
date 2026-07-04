import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.db.models.prediction_history import PredictionHistory
from app.repositories.motor_repository import MotorRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.sensor_data_repository import SensorDataRepository
from app.schemas.prediction import (
    AnomalyResult,
    FaultClassificationResult,
    HealthPredictionResult,
    PredictionHistoryRecord,
    PredictionListResponse,
    PredictionResponse,
    RiskResponse,
)
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.fault_classification_service import FaultClassificationService
from app.services.ml.feature_engineering import FeatureEngineer, MotorFeatures
from app.services.ml.risk_prediction_service import RiskPredictionService

logger = logging.getLogger(__name__)

_MODEL_VERSION = "1.0.0"
_SENSOR_WINDOW = 20  # recent readings used for rolling statistics


class PredictionService:
    """
    Orchestrates the full ML prediction pipeline:
    sensor data → features → anomaly / fault / health / risk → persist.
    """

    def __init__(
        self,
        motor_repo: MotorRepository,
        sensor_repo: SensorDataRepository,
        prediction_repo: PredictionRepository,
        anomaly_svc: AnomalyDetectionService,
        fault_svc: FaultClassificationService,
        risk_svc: RiskPredictionService,
        feature_engineer: FeatureEngineer,
    ) -> None:
        self._motor_repo = motor_repo
        self._sensor_repo = sensor_repo
        self._prediction_repo = prediction_repo
        self._anomaly_svc = anomaly_svc
        self._fault_svc = fault_svc
        self._risk_svc = risk_svc
        self._feature_engineer = feature_engineer

    # ------------------------------------------------------------------
    # POST /api/v1/predict/{motor_id}
    # ------------------------------------------------------------------

    def predict(
        self,
        motor_id: UUID,
        include_features: bool = False,
    ) -> PredictionResponse | None:
        """
        Run full ML pipeline.  Returns None if motor or sensor data is missing.
        """
        motor = self._motor_repo.get_by_id(motor_id)
        if motor is None:
            logger.warning("Motor %s not found", motor_id)
            return None

        readings = self._sensor_repo.get_latest_for_motor(motor_id, limit=_SENSOR_WINDOW)
        if not readings:
            logger.warning("No sensor data for motor %s", motor_id)
            return None

        features = self._feature_engineer.extract(readings, motor)
        if features is None:
            logger.warning("Feature extraction failed for motor %s", motor_id)
            return None

        anomaly = self._anomaly_svc.detect(features)
        fault = self._fault_svc.classify(features)
        health = self._compute_health(features, anomaly, fault)

        history = self._prediction_repo.get_risk_history(motor_id, days=30)
        risk = self._risk_svc.predict_risk(
            current_health=health.health_score,
            history=history,
            anomaly_score=anomaly.score,
            fault_confidence=fault.confidence,
            predicted_fault=fault.fault,
        )

        now = datetime.now(UTC)
        record = self._prediction_repo.create(
            {
                "motor_id": motor_id,
                "predicted_fault": fault.fault if fault.fault != "Normal" else None,
                "confidence": Decimal(str(round(fault.confidence, 2))),
                "health_score": Decimal(str(round(health.health_score, 2))),
                "health_status": health.status,
                "risk_score_7d": Decimal(str(round(risk.risk_7d, 4))),
                "risk_score_30d": Decimal(str(round(risk.risk_30d, 4))),
                "anomaly_detected": anomaly.anomaly,
                "anomaly_score": Decimal(str(round(anomaly.score, 4))),
                "features_used": features.to_dict() if include_features else None,
                "model_version": _MODEL_VERSION,
                "predicted_at": now,
            }
        )

        logger.info(
            "Prediction stored motor=%s id=%s fault=%s health=%.1f risk_7d=%.3f",
            motor_id, record.id, fault.fault, health.health_score, risk.risk_7d,
        )

        return PredictionResponse(
            motor_id=motor_id,
            prediction_id=record.id,
            predicted_at=record.predicted_at,
            anomaly=anomaly,
            fault_classification=fault,
            health=health,
            risk=risk,
            features=features.to_dict() if include_features else None,
            model_version=_MODEL_VERSION,
        )

    # ------------------------------------------------------------------
    # GET /api/v1/motors/{motor_id}/predictions
    # ------------------------------------------------------------------

    def get_predictions(
        self,
        motor_id: UUID,
        limit: int = 50,
        skip: int = 0,
    ) -> PredictionListResponse | None:
        if self._motor_repo.get_by_id(motor_id) is None:
            return None

        records = self._prediction_repo.get_by_motor_id(motor_id, limit=limit, skip=skip)
        total = self._prediction_repo.count_by_motor_id(motor_id)

        return PredictionListResponse(
            motor_id=motor_id,
            total=total,
            items=[PredictionHistoryRecord.model_validate(r) for r in records],
        )

    # ------------------------------------------------------------------
    # GET /api/v1/motors/{motor_id}/risk
    # ------------------------------------------------------------------

    def get_risk(self, motor_id: UUID) -> RiskResponse | None:
        if self._motor_repo.get_by_id(motor_id) is None:
            return None

        latest = self._prediction_repo.get_latest_by_motor_id(motor_id)
        history = self._prediction_repo.get_risk_history(motor_id, days=30)

        if latest is None:
            return RiskResponse(
                motor_id=motor_id,
                current_health_score=100.0,
                risk_7d=0.0,
                risk_30d=0.0,
                risk_level="Low",
                trend="Stable",
                last_predicted_at=None,
                recommendations=["No predictions yet — call POST /api/v1/predict/{motor_id} first"],
            )

        trend = self._compute_trend(history)
        recommendations = self._build_recommendations(latest, trend)

        return RiskResponse(
            motor_id=motor_id,
            current_health_score=float(latest.health_score),
            risk_7d=float(latest.risk_score_7d),
            risk_30d=float(latest.risk_score_30d),
            risk_level=self._risk_svc.classify_level(
                float(latest.risk_score_7d),
                float(latest.risk_score_30d),
            ),
            trend=trend,
            last_predicted_at=latest.predicted_at,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_health(
        features: MotorFeatures,
        anomaly: AnomalyResult,
        fault: FaultClassificationResult,
    ) -> HealthPredictionResult:
        """
        Composite health score (0–100):
          - Rule-based thresholds from Module 3 HealthScoreService
          - Anomaly penalty (up to −25 points)
          - Fault confidence penalty (up to −15 points)
        """
        rule_score = 100.0

        if features.temperature > 90:
            rule_score -= 20
        elif features.temperature > 80:
            rule_score -= 10

        if features.vibration > 7:
            rule_score -= 20
        elif features.vibration > 5:
            rule_score -= 10

        if features.current_ratio > 1.0:
            rule_score -= 15
        elif features.current_ratio > 0.9:
            rule_score -= 7

        anomaly_penalty = anomaly.score * 25.0
        fault_penalty = (fault.confidence / 100.0) * 15.0 if fault.fault != "Normal" else 0.0

        health_score = max(0.0, min(100.0, rule_score - anomaly_penalty - fault_penalty))

        if health_score >= 75:
            status = "Healthy"
        elif health_score >= 50:
            status = "Warning"
        else:
            status = "Critical"

        return HealthPredictionResult(health_score=round(health_score, 2), status=status)

    @staticmethod
    def _compute_trend(history: Sequence[PredictionHistory]) -> str:
        if len(history) < 3:
            return "Stable"
        sorted_h = sorted(history, key=lambda h: h.predicted_at)
        values = [float(h.health_score) for h in sorted_h[-10:]]
        delta = values[-1] - values[0]
        if delta <= -5:
            return "Degrading"
        if delta >= 5:
            return "Improving"
        return "Stable"

    @staticmethod
    def _build_recommendations(latest: PredictionHistory, trend: str) -> list[str]:
        recs: list[str] = []

        if latest.anomaly_detected:
            recs.append("Anomaly detected — schedule immediate inspection")
        if latest.predicted_fault:
            recs.append(f"Active fault: {latest.predicted_fault} — consult maintenance procedure")
        r7 = float(latest.risk_score_7d)
        r30 = float(latest.risk_score_30d)
        if r7 >= 0.70:
            recs.append("Critical 7-day failure risk — initiate emergency maintenance now")
        elif r7 >= 0.40:
            recs.append("High short-term risk — schedule maintenance within 48 hours")
        elif r7 >= 0.20:
            recs.append("Elevated 7-day risk — plan maintenance this week")
        if r30 >= 0.60:
            recs.append("High 30-day failure risk — schedule preventive maintenance within 2 weeks")
        h = float(latest.health_score)
        if h < 50:
            recs.append("Critical health score — conduct motor replacement assessment")
        elif h < 75:
            recs.append("Health in warning zone — increase monitoring frequency")
        if trend == "Degrading":
            recs.append("Degrading health trend — investigate root cause and lubrication schedule")
        if not recs:
            recs.append("Motor operating within normal parameters — continue routine monitoring")

        return recs
