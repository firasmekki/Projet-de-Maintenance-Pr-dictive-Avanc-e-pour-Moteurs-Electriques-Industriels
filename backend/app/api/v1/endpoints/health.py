from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.dependencies import get_settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        timestamp=datetime.now(UTC),
    )
