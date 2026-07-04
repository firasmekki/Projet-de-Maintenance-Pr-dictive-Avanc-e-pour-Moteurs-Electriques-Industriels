import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session
from app.schemas.prediction import (
    PredictionListResponse,
    PredictionRequest,
    PredictionResponse,
    RiskResponse,
)
from app.services.ml.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["predictions"])


def _get_prediction_service(
    session: AsyncSession = Depends(get_session),
) -> PredictionService:
    return PredictionService(session)


@router.post(
    "/predict/{motor_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Run ML prediction pipeline for a motor",
    description=(
        "Executes anomaly detection (Isolation Forest), fault classification (Random Forest), "
        "health score computation, and 7/30-day risk prediction. "
        "Persists result to prediction_history."
    ),
)
async def predict_motor(
    motor_id: UUID,
    request: PredictionRequest = PredictionRequest(),
    service: PredictionService = Depends(_get_prediction_service),
) -> PredictionResponse:
    try:
        return await service.predict(motor_id, include_features=request.include_features)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception:
        logger.exception("Unhandled prediction error for motor %s", motor_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction engine error — check logs",
        )


@router.get(
    "/motors/{motor_id}/predictions",
    response_model=PredictionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List prediction history for a motor",
)
async def list_predictions(
    motor_id: UUID,
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    service: PredictionService = Depends(_get_prediction_service),
) -> PredictionListResponse:
    try:
        return await service.get_predictions(motor_id, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


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
async def get_motor_risk(
    motor_id: UUID,
    service: PredictionService = Depends(_get_prediction_service),
) -> RiskResponse:
    try:
        return await service.get_risk(motor_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
