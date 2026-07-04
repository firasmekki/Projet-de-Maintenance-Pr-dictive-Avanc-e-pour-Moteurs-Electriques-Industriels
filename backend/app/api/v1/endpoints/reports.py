"""Reports endpoints: list, get, delete and export."""
from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.analysis_report_repository import AnalysisReportRepository
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


@router.get("/reports", summary="List recent analysis reports")
def list_reports(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    repo    = AnalysisReportRepository(db)
    reports = repo.get_recent(limit)
    entries = []
    for r in reports:
        analysis = json.loads(r.analysis_json) if r.analysis_json else {}
        entries.append({
            "report_id":    str(r.id),
            "filename":     r.filename,
            "status":       r.status,
            "row_count":    r.row_count,
            "quality_score": r.quality_score,
            "health_score": analysis.get("health_score"),
            "risk_7d":      analysis.get("risk", {}).get("days_7"),
            "fault":        analysis.get("fault"),
            "severity":     analysis.get("severity"),
            "created_at":   r.created_at.isoformat(),
            "analyzed_at":  r.analyzed_at.isoformat() if r.analyzed_at else None,
        })
    return {"reports": entries}


@router.get("/reports/{report_id}", summary="Retrieve a full analysis report")
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    repo   = AnalysisReportRepository(db)
    report = repo.get_by_id(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    analysis = json.loads(report.analysis_json) if report.analysis_json else None
    columns  = json.loads(report.columns_json)  if report.columns_json  else []
    preview  = json.loads(report.dataset_json)[:50] if report.dataset_json else []

    return {
        "report_id":      str(report.id),
        "filename":       report.filename,
        "file_size":      report.file_size,
        "row_count":      report.row_count,
        "column_count":   report.column_count,
        "missing_values": report.missing_values,
        "quality_score":  report.quality_score,
        "status":         report.status,
        "columns":        columns,
        "preview":        preview,
        "analysis":       analysis,
        "ai_narrative":   report.ai_narrative,
        "created_at":     report.created_at.isoformat(),
        "analyzed_at":    report.analyzed_at.isoformat() if report.analyzed_at else None,
    }


@router.delete("/reports/{report_id}", summary="Delete a report")
def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> Response:
    repo    = AnalysisReportRepository(db)
    deleted = repo.delete(report_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return Response(status_code=204)


@router.get("/export/json/{report_id}", summary="Download full report as JSON")
def export_json(report_id: UUID, db: Session = Depends(get_db)) -> Response:
    report = _get_or_404(report_id, db)
    data   = ExportService().to_json(report)
    return Response(
        content=data, media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="orbit_report_{report_id}.json"'},
    )


@router.get("/export/csv/{report_id}", summary="Download processed dataset as CSV")
def export_csv(report_id: UUID, db: Session = Depends(get_db)) -> Response:
    report = _get_or_404(report_id, db)
    data   = ExportService().to_csv(report)
    return Response(
        content=data, media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="orbit_dataset_{report_id}.csv"'},
    )


@router.get("/export/xlsx/{report_id}", summary="Download full report as Excel")
def export_xlsx(report_id: UUID, db: Session = Depends(get_db)) -> Response:
    report = _get_or_404(report_id, db)
    data   = ExportService().to_xlsx(report)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="orbit_report_{report_id}.xlsx"'},
    )


@router.get("/export/pdf/{report_id}", summary="Download full report as PDF")
def export_pdf(report_id: UUID, db: Session = Depends(get_db)) -> Response:
    report = _get_or_404(report_id, db)
    data   = ExportService().to_pdf(report)
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="orbit_report_{report_id}.pdf"'},
    )


def _get_or_404(report_id: UUID, db: Session):
    repo   = AnalysisReportRepository(db)
    report = repo.get_by_id(report_id)
    if report is None or report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or analysis not yet complete",
        )
    return report
