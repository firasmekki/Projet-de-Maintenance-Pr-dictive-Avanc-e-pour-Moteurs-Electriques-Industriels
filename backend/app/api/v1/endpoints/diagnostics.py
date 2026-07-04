from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_diagnostic_service
from app.schemas.diagnostics import DiagnosticResponse
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/diagnose", tags=["diagnostics"])


@router.post("/{motor_id}", response_model=DiagnosticResponse, summary="Run motor diagnosis")
async def diagnose_motor(
    motor_id: UUID,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticResponse:
    diagnosis = diagnostic_service.diagnose(motor_id, persist=True)
    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} or its sensor data was not found",
        )
    return diagnosis
