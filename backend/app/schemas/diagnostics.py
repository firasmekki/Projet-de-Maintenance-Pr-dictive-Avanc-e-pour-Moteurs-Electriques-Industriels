from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FaultHistoryResponse(BaseModel):
    id: UUID
    motor_id: UUID
    fault_type: str
    severity: str
    confidence: Decimal
    description: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaultHistoryListResponse(BaseModel):
    motor_id: UUID
    count: int
    items: list[FaultHistoryResponse]


class TrendWindowResponse(BaseModel):
    temperature: str
    vibration: str
    current: str


class TrendAnalysisResponse(BaseModel):
    last_24h: TrendWindowResponse
    last_7d: TrendWindowResponse
    last_30d: TrendWindowResponse


class DiagnosticResponse(BaseModel):
    motor_id: UUID
    health_score: int = Field(ge=0, le=100)
    fault: str
    severity: str
    confidence: int = Field(ge=0, le=100)
    risk_level: str
    recommendation: str
    description: str
    trends: TrendAnalysisResponse
