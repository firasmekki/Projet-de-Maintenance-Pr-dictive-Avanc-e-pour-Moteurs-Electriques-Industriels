from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings as get_cached_settings
from app.db.session import get_db
from app.repositories.fault_repository import FaultRepository
from app.repositories.maintenance_repository import MaintenanceRepository
from app.repositories.motor_repository import MotorRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.sensor_data_repository import SensorDataRepository
from app.services.diagnostic_service import DiagnosticService
from app.services.fault_scoring_service import FaultScoringService
from app.services.health_score_service import HealthScoreService
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.fault_classification_service import FaultClassificationService
from app.services.ml.feature_engineering import FeatureEngineer
from app.services.ml.prediction_service import PredictionService
from app.services.ml.risk_prediction_service import RiskPredictionService
from app.services.monitoring_service import MonitoringService
from app.services.motor_service import MotorService
from app.services.trend_analysis_service import TrendAnalysisService


def get_settings() -> Settings:
    return get_cached_settings()


def get_request_context() -> Generator[dict[str, str], None, None]:
    yield {"service": "orbit-ai-backend"}


def get_motor_repository(db: Session = Depends(get_db)) -> MotorRepository:
    return MotorRepository(db)


def get_sensor_data_repository(db: Session = Depends(get_db)) -> SensorDataRepository:
    return SensorDataRepository(db)


def get_fault_repository(db: Session = Depends(get_db)) -> FaultRepository:
    return FaultRepository(db)


def get_maintenance_repository(db: Session = Depends(get_db)) -> MaintenanceRepository:
    return MaintenanceRepository(db)


def get_recommendation_repository(db: Session = Depends(get_db)) -> RecommendationRepository:
    return RecommendationRepository(db)


def get_motor_service(
    motor_repository: MotorRepository = Depends(get_motor_repository),
) -> MotorService:
    return MotorService(motor_repository)


def get_monitoring_service(
    sensor_data_repository: SensorDataRepository = Depends(get_sensor_data_repository),
) -> MonitoringService:
    return MonitoringService(sensor_data_repository)


def get_health_score_service() -> HealthScoreService:
    return HealthScoreService()


def get_fault_scoring_service() -> FaultScoringService:
    return FaultScoringService()


def get_trend_analysis_service(
    sensor_data_repository: SensorDataRepository = Depends(get_sensor_data_repository),
) -> TrendAnalysisService:
    return TrendAnalysisService(sensor_data_repository)


def get_diagnostic_service(
    motor_service: MotorService = Depends(get_motor_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    health_score_service: HealthScoreService = Depends(get_health_score_service),
    fault_scoring_service: FaultScoringService = Depends(get_fault_scoring_service),
    trend_analysis_service: TrendAnalysisService = Depends(get_trend_analysis_service),
    fault_repository: FaultRepository = Depends(get_fault_repository),
) -> DiagnosticService:
    return DiagnosticService(
        motor_service=motor_service,
        monitoring_service=monitoring_service,
        health_score_service=health_score_service,
        fault_scoring_service=fault_scoring_service,
        trend_analysis_service=trend_analysis_service,
        fault_repository=fault_repository,
    )


def get_prediction_repository(db: Session = Depends(get_db)) -> PredictionRepository:
    return PredictionRepository(db)


def get_anomaly_detection_service() -> AnomalyDetectionService:
    return AnomalyDetectionService()


def get_fault_classification_service() -> FaultClassificationService:
    return FaultClassificationService()


def get_risk_prediction_service() -> RiskPredictionService:
    return RiskPredictionService()


def get_feature_engineer() -> FeatureEngineer:
    return FeatureEngineer()


def get_prediction_service(
    motor_repo: MotorRepository = Depends(get_motor_repository),
    sensor_repo: SensorDataRepository = Depends(get_sensor_data_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    anomaly_svc: AnomalyDetectionService = Depends(get_anomaly_detection_service),
    fault_svc: FaultClassificationService = Depends(get_fault_classification_service),
    risk_svc: RiskPredictionService = Depends(get_risk_prediction_service),
    feature_engineer: FeatureEngineer = Depends(get_feature_engineer),
) -> PredictionService:
    return PredictionService(
        motor_repo=motor_repo,
        sensor_repo=sensor_repo,
        prediction_repo=prediction_repo,
        anomaly_svc=anomaly_svc,
        fault_svc=fault_svc,
        risk_svc=risk_svc,
        feature_engineer=feature_engineer,
    )


__all__ = [
    "get_db",
    "get_anomaly_detection_service",
    "get_diagnostic_service",
    "get_fault_classification_service",
    "get_fault_repository",
    "get_fault_scoring_service",
    "get_feature_engineer",
    "get_health_score_service",
    "get_maintenance_repository",
    "get_motor_repository",
    "get_motor_service",
    "get_monitoring_service",
    "get_prediction_repository",
    "get_prediction_service",
    "get_recommendation_repository",
    "get_request_context",
    "get_risk_prediction_service",
    "get_sensor_data_repository",
    "get_settings",
    "get_trend_analysis_service",
]
