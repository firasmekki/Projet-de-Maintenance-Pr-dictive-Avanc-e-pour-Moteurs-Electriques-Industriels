from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnomalyResult(BaseModel):
    anomaly: bool
    score: float = Field(..., ge=0.0, le=1.0, description="0 = normal, 1 = highly anomalous")


class FaultClassificationResult(BaseModel):
    fault: str
    confidence: float = Field(..., ge=0.0, le=100.0, description="Confidence as percentage 0-100")
    all_probabilities: Dict[str, float] = Field(default_factory=dict)


class HealthPredictionResult(BaseModel):
    health_score: float = Field(..., ge=0.0, le=100.0)
    status: str = Field(..., description="Healthy | Warning | Critical")


class RiskPredictionResult(BaseModel):
    risk_7d: float = Field(..., ge=0.0, le=1.0, description="Failure probability in 7 days")
    risk_30d: float = Field(..., ge=0.0, le=1.0, description="Failure probability in 30 days")
    risk_level: str = Field(..., description="Low | Medium | High | Critical")


class PredictionRequest(BaseModel):
    include_features: bool = Field(default=False, description="Return raw feature values in response")


class PredictionResponse(BaseModel):
    motor_id: UUID
    prediction_id: UUID
    prediction_date: datetime
    anomaly: AnomalyResult
    fault_classification: FaultClassificationResult
    health: HealthPredictionResult
    risk: RiskPredictionResult
    features: Optional[Dict[str, float]] = None
    model_version: str

    model_config = {"from_attributes": True}


class PredictionHistoryRecord(BaseModel):
    id: UUID
    motor_id: UUID
    predicted_fault: Optional[str]
    confidence: Optional[float]
    health_score: float
    health_status: str
    risk_score_7d: float
    risk_score_30d: float
    anomaly_detected: bool
    anomaly_score: Optional[float]
    model_version: Optional[str]
    prediction_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    motor_id: UUID
    total: int
    predictions: List[PredictionHistoryRecord]


class RiskResponse(BaseModel):
    motor_id: UUID
    current_health_score: float
    risk_7d: float
    risk_30d: float
    risk_level: str
    trend: str = Field(..., description="Improving | Stable | Degrading")
    last_prediction: Optional[datetime]
    recommendations: List[str]
