import logging
import uuid
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.prediction_history import PredictionHistory
from app.database.repositories.motor_repository import MotorRepository
from app.database.repositories.prediction_repository import PredictionRepository
from app.database.repositories.sensor_data_repository import SensorDataRepository
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

MODEL_VERSION = "1.0.0"
SENSOR_WINDOW = 20  # number of recent readings used for rolling stats


class PredictionService:
    """Orchestrates the full ML prediction pipeline for a motor."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._motor_repo = MotorRepository(session)
        self._sensor_repo = SensorDataRepository(session)
        self._prediction_repo = PredictionRepository(session)
        self._feature_engineer = FeatureEngineer()
        self._anomaly_svc = AnomalyDetectionService()
        self._fault_svc = FaultClassificationService()
        self._risk_svc = RiskPredictionService()

    # ------------------------------------------------------------------
    # POST /api/v1/predict/{motor_id}
    # ------------------------------------------------------------------

    async def predict(
        self,
        motor_id: UUID,
        include_features: bool = False,
    ) -> PredictionResponse:
        motor = await self._motor_repo.get_by_id(motor_id)
        if motor is None:
            raise ValueError(f"Motor {motor_id} not found")

        readings = await self._sensor_repo.get_recent(motor_id, limit=SENSOR_WINDOW)
        if not readings:
            raise ValueError(f"No sensor data found for motor {motor_id}")

        features = self._feature_engineer.extract(
            readings=readings,
            rated_current=float(motor.rated_current),
            rated_voltage=float(motor.rated_voltage),
        )
        if features is None:
            raise ValueError("Feature extraction returned no result")

        anomaly = self._anomaly_svc.detect(features)
        fault = self._fault_svc.classify(features)
        health = self._compute_health(features, anomaly, fault)

        history = await self._prediction_repo.get_risk_history(motor_id, days=30)
        risk = self._risk_svc.predict_risk(
            current_health=health.health_score,
            history=history,
            anomaly_score=anomaly.score,
            fault_confidence=fault.confidence,
            predicted_fault=fault.fault,
        )

        record = PredictionHistory(
            id=uuid.uuid4(),
            motor_id=motor_id,
            predicted_fault=fault.fault if fault.fault != "Normal" else None,
            confidence=fault.confidence,
            health_score=health.health_score,
            health_status=health.status,
            risk_score_7d=risk.risk_7d,
            risk_score_30d=risk.risk_30d,
            anomaly_detected=anomaly.anomaly,
            anomaly_score=anomaly.score,
            features_used=features.to_dict() if include_features else None,
            model_version=MODEL_VERSION,
            prediction_date=datetime.utcnow(),
        )
        await self._prediction_repo.create(record)

        logger.info(
            "Prediction completed motor=%s fault=%s health=%.1f risk_7d=%.2f",
            motor_id,
            fault.fault,
            health.health_score,
            risk.risk_7d,
        )

        return PredictionResponse(
            motor_id=motor_id,
            prediction_id=record.id,
            prediction_date=record.prediction_date,
            anomaly=anomaly,
            fault_classification=fault,
            health=health,
            risk=risk,
            features=features.to_dict() if include_features else None,
            model_version=MODEL_VERSION,
        )

    # ------------------------------------------------------------------
    # GET /api/v1/motors/{motor_id}/predictions
    # ------------------------------------------------------------------

    async def get_predictions(
        self,
        motor_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> PredictionListResponse:
        if not await self._motor_repo.exists(motor_id):
            raise ValueError(f"Motor {motor_id} not found")

        records = await self._prediction_repo.get_by_motor_id(motor_id, limit=limit, offset=offset)
        total = await self._prediction_repo.count_by_motor_id(motor_id)

        return PredictionListResponse(
            motor_id=motor_id,
            total=total,
            predictions=[PredictionHistoryRecord.model_validate(r) for r in records],
        )

    # ------------------------------------------------------------------
    # GET /api/v1/motors/{motor_id}/risk
    # ------------------------------------------------------------------

    async def get_risk(self, motor_id: UUID) -> RiskResponse:
        if not await self._motor_repo.exists(motor_id):
            raise ValueError(f"Motor {motor_id} not found")

        latest = await self._prediction_repo.get_latest_by_motor_id(motor_id)
        history = await self._prediction_repo.get_risk_history(motor_id, days=30)

        if latest is None:
            return RiskResponse(
                motor_id=motor_id,
                current_health_score=100.0,
                risk_7d=0.0,
                risk_30d=0.0,
                risk_level="Low",
                trend="Stable",
                last_prediction=None,
                recommendations=["No predictions yet — call POST /predict/{motor_id} first"],
            )

        trend = self._compute_trend(history)
        recommendations = self._build_recommendations(latest, trend)

        return RiskResponse(
            motor_id=motor_id,
            current_health_score=latest.health_score,
            risk_7d=latest.risk_score_7d,
            risk_30d=latest.risk_score_30d,
            risk_level=self._risk_svc.classify_level(latest.risk_score_7d, latest.risk_score_30d),
            trend=trend,
            last_prediction=latest.prediction_date,
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
        Composite health score:
          50% rule-based thresholds (Module 3 logic, unchanged for backward compatibility)
          30% anomaly penalty
          20% fault confidence penalty
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
    def _compute_trend(history: List[PredictionHistory]) -> str:
        if len(history) < 3:
            return "Stable"
        sorted_h = sorted(history, key=lambda h: h.prediction_date)
        values = [h.health_score for h in sorted_h[-10:]]
        delta = values[-1] - values[0]
        if delta <= -5:
            return "Degrading"
        if delta >= 5:
            return "Improving"
        return "Stable"

    @staticmethod
    def _build_recommendations(
        latest: PredictionHistory,
        trend: str,
    ) -> List[str]:
        recs: List[str] = []

        if latest.anomaly_detected:
            recs.append("Anomaly detected — schedule immediate inspection")
        if latest.predicted_fault:
            recs.append(f"Active fault: {latest.predicted_fault} — consult maintenance procedure")
        if latest.risk_score_7d >= 0.70:
            recs.append("Critical 7-day failure risk — initiate emergency maintenance")
        elif latest.risk_score_7d >= 0.40:
            recs.append("High short-term risk — schedule maintenance within 48 hours")
        elif latest.risk_score_7d >= 0.20:
            recs.append("Elevated 7-day risk — monitor closely, plan maintenance this week")
        if latest.risk_score_30d >= 0.60:
            recs.append("High 30-day failure risk — schedule preventive maintenance within 2 weeks")
        if latest.health_score < 50:
            recs.append("Critical health score — conduct motor replacement assessment")
        elif latest.health_score < 75:
            recs.append("Health in warning zone — increase monitoring to hourly intervals")
        if trend == "Degrading":
            recs.append("Degrading health trend — investigate root cause and lubrication schedule")
        if not recs:
            recs.append("Motor operating within normal parameters — continue routine monitoring")

        return recs
