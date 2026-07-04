import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_prediction_service
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
    RiskResponse,
)
from app.services.ml.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])


@router.post(
    "/predict/{motor_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run ML prediction pipeline for a motor",
    description=(
        "Executes anomaly detection (Isolation Forest), fault classification (Random Forest), "
        "composite health scoring, and 7/30-day risk prediction. "
        "Persists the result to prediction_history."
    ),
)
def predict_motor(
    motor_id: UUID,
    request: PredictionRequest = PredictionRequest(),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    result = prediction_service.predict(motor_id, include_features=request.include_features)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} or its sensor data was not found",
        )
    return result


@router.get(
    "/motors/{motor_id}/predictions",
    response_model=PredictionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List prediction history for a motor",
)
def list_predictions(
    motor_id: UUID,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum records to return"),
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionListResponse:
    result = prediction_service.get_predictions(motor_id, limit=limit, skip=skip)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} not found",
        )
    return result


@router.get(
    "/motors/{motor_id}/risk",
    response_model=RiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Current risk assessment for a motor",
    description=(
        "Returns the latest failure probability scores (7-day and 30-day), "
        "health trend, risk level classification, and actionable recommendations."
    ),
)
def get_motor_risk(
    motor_id: UUID,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> RiskResponse:
    result = prediction_service.get_risk(motor_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} not found",
        )
    return result
