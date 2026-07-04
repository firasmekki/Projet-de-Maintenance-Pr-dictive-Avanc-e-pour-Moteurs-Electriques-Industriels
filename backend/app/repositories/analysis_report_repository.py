from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select

from app.db.models.analysis_report import AnalysisReport
from app.repositories.base import BaseRepository


class AnalysisReportRepository(BaseRepository[AnalysisReport]):
    model = AnalysisReport

    def get_recent(self, limit: int = 20) -> Sequence[AnalysisReport]:
        stmt = (
            select(AnalysisReport)
            .order_by(desc(AnalysisReport.created_at))
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def get_by_status(self, status: str, limit: int = 100) -> Sequence[AnalysisReport]:
        stmt = (
            select(AnalysisReport)
            .where(AnalysisReport.status == status)
            .order_by(desc(AnalysisReport.created_at))
            .limit(limit)
        )
        return self.db.scalars(stmt).all()
