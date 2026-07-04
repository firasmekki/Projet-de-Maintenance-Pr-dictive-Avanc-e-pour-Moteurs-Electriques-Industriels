"""POST /api/v1/reports/{id}/multi-agent — Multi-expert agent analysis."""
from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.analysis_report_repository import AnalysisReportRepository
from app.services.multi_agent_service import MultiAgentService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["multi-agent"])


@router.post("/reports/{report_id}/multi-agent", summary="Run multi-expert agent analysis")
def run_multi_agent(report_id: UUID, db: Session = Depends(get_db)) -> dict:
    repo   = AnalysisReportRepository(db)
    report = repo.get_by_id(report_id)

    if report is None or report.status != "completed":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found or not completed")

    if not report.analysis_json:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No analysis data")

    analysis = json.loads(report.analysis_json)
    svc      = MultiAgentService()
    result   = svc.analyze(analysis)
    return result
