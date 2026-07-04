"""POST /api/v1/upload  and  POST /api/v1/analyze/{report_id}"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.analysis_report_repository import AnalysisReportRepository
from app.services.ai_narrative_service import AINarrativeService
from app.services.analysis_pipeline_service import AnalysisPipelineService
from app.services.dataset_service import DatasetService, DatasetValidationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_ALLOWED_EXTS  = {"csv", "xlsx", "xls", "json"}


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    report_id:     str
    filename:      str
    file_size:     int
    row_count:     int
    column_count:  int
    missing_values: int
    quality_score: float
    columns:       list[str]
    preview:       list[dict]
    status:        str


class AnalyzeResponse(BaseModel):
    report_id:    str
    status:       str
    analysis:     dict
    ai_narrative: str | None


class MotorProfileInput(BaseModel):
    name:               str   | None = None
    manufacturer:       str   | None = None   # Siemens, ABB, Schneider, WEG...
    nominal_power_kw:   float | None = None
    nominal_voltage_v:  float | None = None
    nominal_current_a:  float | None = None   # key → improves current ratio accuracy
    nominal_speed_rpm:  float | None = None
    insulation_class:   str   | None = None   # B, F, H
    efficiency_class:   str   | None = None   # IE2, IE3, IE4
    protection_class:   str   | None = None   # IP44, IP54, IP55


class AnalyzeRequest(BaseModel):
    motor_profile: MotorProfileInput | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a sensor dataset (CSV / XLSX / JSON)",
)
async def upload_dataset(
    file: UploadFile = File(..., description="Sensor dataset file"),
    db:   Session    = Depends(get_db),
) -> UploadResponse:
    # ---- Validate extension -------------------------------------------
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type .{ext}. Allowed: {sorted(_ALLOWED_EXTS)}",
        )

    # ---- Read content ------------------------------------------------
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE // 1024 // 1024} MB",
        )

    # ---- Parse & validate --------------------------------------------
    svc = DatasetService()
    try:
        summary = svc.process(content, file.filename or "upload")
    except DatasetValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # ---- Persist to DB -----------------------------------------------
    repo   = AnalysisReportRepository(db)
    report = repo.create({
        "filename":       file.filename or "upload",
        "file_size":      len(content),
        "row_count":      summary["row_count"],
        "column_count":   summary["column_count"],
        "missing_values": summary["missing_values"],
        "quality_score":  summary["quality_score"],
        "status":         "uploaded",
        "columns_json":   json.dumps(summary["columns"]),
        "dataset_json":   json.dumps(summary["records"]),
        "created_at":     datetime.now(UTC),
    })

    logger.info(
        "Dataset uploaded: %s  id=%s  rows=%d  cols=%d",
        file.filename, report.id, summary["row_count"], summary["column_count"],
    )

    return UploadResponse(
        report_id=      str(report.id),
        filename=       report.filename,
        file_size=      report.file_size,
        row_count=      report.row_count,
        column_count=   report.column_count,
        missing_values= report.missing_values,
        quality_score=  report.quality_score,
        columns=        summary["columns"],
        preview=        summary["preview"],
        status=         report.status,
    )


@router.post(
    "/analyze/{report_id}",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full ML + diagnostic analysis pipeline on an uploaded dataset",
)
def analyze_dataset(
    report_id:  UUID,
    request:    AnalyzeRequest | None = None,
    db:         Session = Depends(get_db),
) -> AnalyzeResponse:
    repo   = AnalysisReportRepository(db)
    report = repo.get_by_id(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    if not report.dataset_json:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No dataset available for this report",
        )

    motor_profile = request.motor_profile.model_dump() if (request and request.motor_profile) else None

    # Mark as analyzing
    repo.update(report_id, {"status": "analyzing"})

    try:
        records  = json.loads(report.dataset_json)
        pipeline = AnalysisPipelineService()
        analysis = pipeline.analyze(records, motor_profile=motor_profile)

        narrative_svc = AINarrativeService()
        narrative     = narrative_svc.generate(report.filename, analysis)

        repo.update(report_id, {
            "status":        "completed",
            "analysis_json": json.dumps(analysis),
            "ai_narrative":  narrative,
            "analyzed_at":   datetime.now(UTC),
        })

        logger.info("Analysis completed: report=%s fault=%s health=%s",
                    report_id, analysis.get("fault"), analysis.get("health_score"))

        return AnalyzeResponse(
            report_id=    str(report_id),
            status=       "completed",
            analysis=     analysis,
            ai_narrative= narrative,
        )

    except Exception as exc:
        logger.exception("Analysis failed for report %s", report_id)
        repo.update(report_id, {
            "status":        "failed",
            "error_message": str(exc),
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc
