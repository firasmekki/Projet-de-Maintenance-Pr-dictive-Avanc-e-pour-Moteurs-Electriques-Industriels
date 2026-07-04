from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.repositories.fault_repository import FaultRepository
from app.schemas.diagnostics import DiagnosticResponse
from app.services.fault_scoring_service import FaultScoringService
from app.services.health_score_service import HealthScoreService
from app.services.monitoring_service import MonitoringService
from app.services.motor_service import MotorService
from app.services.trend_analysis_service import TrendAnalysisService


class DiagnosticService:
    def __init__(
        self,
        motor_service: MotorService,
        monitoring_service: MonitoringService,
        health_score_service: HealthScoreService,
        fault_scoring_service: FaultScoringService,
        trend_analysis_service: TrendAnalysisService,
        fault_repository: FaultRepository,
    ) -> None:
        self.motor_service = motor_service
        self.monitoring_service = monitoring_service
        self.health_score_service = health_score_service
        self.fault_scoring_service = fault_scoring_service
        self.trend_analysis_service = trend_analysis_service
        self.fault_repository = fault_repository

    def diagnose(self, motor_id: UUID, persist: bool = True) -> DiagnosticResponse | None:
        motor = self.motor_service.get_motor(motor_id)
        if motor is None:
            return None

        latest = self.monitoring_service.get_latest_sensor_data(motor_id)
        if latest is None:
            return None

        trends = self.trend_analysis_service.analyze(motor_id)
        fault_score = self.fault_scoring_service.score(motor, latest, trends)
        health = self.health_score_service.calculate(motor, latest)

        if persist and fault_score.fault != "No Fault Detected":
            self.fault_repository.create(
                {
                    "motor_id": motor_id,
                    "fault_type": fault_score.fault,
                    "severity": fault_score.severity,
                    "confidence": Decimal(fault_score.confidence),
                    "description": fault_score.description,
                    "detected_at": datetime.now(UTC),
                }
            )

        return DiagnosticResponse(
            motor_id=motor_id,
            health_score=health.health_score,
            fault=fault_score.fault,
            severity=fault_score.severity,
            confidence=fault_score.confidence,
            risk_level=fault_score.risk_level,
            recommendation=fault_score.recommendation,
            description=fault_score.description,
            trends=trends,
        )
