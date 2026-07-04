from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_diagnostic_service,
    get_fault_repository,
    get_health_score_service,
    get_monitoring_service,
    get_motor_service,
)
from app.repositories.fault_repository import FaultRepository
from app.schemas.diagnostics import DiagnosticResponse, FaultHistoryListResponse
from app.schemas.monitoring import (
    HealthResponse,
    LatestSensorDataResponse,
    MotorDetailsResponse,
    MotorResponse,
    SensorDataListResponse,
)
from app.services.health_score_service import HealthScoreService
from app.services.monitoring_service import MonitoringService
from app.services.motor_service import MotorService
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/motors", tags=["motors"])


@router.get("", response_model=list[MotorResponse], summary="List motors")
async def list_motors(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    motor_service: MotorService = Depends(get_motor_service),
) -> list[MotorResponse]:
    return list(motor_service.list_motors(skip=skip, limit=limit))


@router.get("/{motor_id}", response_model=MotorDetailsResponse, summary="Get motor details")
async def get_motor_details(
    motor_id: UUID,
    motor_service: MotorService = Depends(get_motor_service),
) -> MotorDetailsResponse:
    stats = motor_service.get_motor_with_stats(motor_id)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} was not found",
        )

    motor = stats["motor"]
    return MotorDetailsResponse(
        id=motor.id,
        name=motor.name,
        manufacturer=motor.manufacturer,
        model=motor.model,
        rated_power_kw=motor.rated_power_kw,
        rated_voltage=motor.rated_voltage,
        rated_current=motor.rated_current,
        rpm=motor.rpm,
        location=motor.location,
        status=motor.status,
        created_at=motor.created_at,
        updated_at=motor.updated_at,
        latest_sensor_values=stats["latest_sensor_data"],
        total_faults=stats["total_faults"],
        total_maintenance_events=stats["total_maintenance_events"],
    )


@router.get(
    "/{motor_id}/sensor-data",
    response_model=SensorDataListResponse,
    summary="Get motor sensor history",
)
async def get_sensor_data(
    motor_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
    motor_service: MotorService = Depends(get_motor_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
) -> SensorDataListResponse:
    if motor_service.get_motor(motor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} was not found",
        )

    items = list(monitoring_service.get_sensor_history(motor_id, skip=skip, limit=limit))
    return SensorDataListResponse(motor_id=motor_id, count=len(items), items=items)


@router.get(
    "/{motor_id}/latest",
    response_model=LatestSensorDataResponse,
    summary="Get latest sensor values",
)
async def get_latest_sensor_data(
    motor_id: UUID,
    motor_service: MotorService = Depends(get_motor_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
) -> LatestSensorDataResponse:
    if motor_service.get_motor(motor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} was not found",
        )

    latest = monitoring_service.get_latest_sensor_data(motor_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data exists for motor {motor_id}",
        )

    return LatestSensorDataResponse(motor_id=motor_id, latest=latest)


@router.get("/{motor_id}/health", response_model=HealthResponse, summary="Get motor health score")
async def get_motor_health(
    motor_id: UUID,
    motor_service: MotorService = Depends(get_motor_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    health_score_service: HealthScoreService = Depends(get_health_score_service),
) -> HealthResponse:
    motor = motor_service.get_motor(motor_id)
    if motor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} was not found",
        )

    latest = monitoring_service.get_latest_sensor_data(motor_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data exists for motor {motor_id}",
        )

    return health_score_service.calculate(motor, latest)


@router.get(
    "/{motor_id}/faults",
    response_model=FaultHistoryListResponse,
    summary="Get motor fault history",
)
async def get_motor_faults(
    motor_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    motor_service: MotorService = Depends(get_motor_service),
    fault_repository: FaultRepository = Depends(get_fault_repository),
) -> FaultHistoryListResponse:
    if motor_service.get_motor(motor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} was not found",
        )

    items = list(fault_repository.get_for_motor(motor_id, limit=limit))
    return FaultHistoryListResponse(motor_id=motor_id, count=len(items), items=items)


@router.get(
    "/{motor_id}/diagnosis",
    response_model=DiagnosticResponse,
    summary="Get current motor diagnosis without storing a new fault",
)
async def get_current_motor_diagnosis(
    motor_id: UUID,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticResponse:
    diagnosis = diagnostic_service.diagnose(motor_id, persist=False)
    if diagnosis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Motor {motor_id} or its sensor data was not found",
        )
    return diagnosis
