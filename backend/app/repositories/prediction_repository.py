from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, func, select

from app.db.models.prediction_history import PredictionHistory
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[PredictionHistory]):
    model = PredictionHistory

    def get_by_motor_id(
        self,
        motor_id: UUID,
        limit: int = 50,
        skip: int = 0,
    ) -> Sequence[PredictionHistory]:
        statement = (
            select(PredictionHistory)
            .where(PredictionHistory.motor_id == motor_id)
            .order_by(desc(PredictionHistory.predicted_at))
            .limit(limit)
            .offset(skip)
        )
        return self.db.scalars(statement).all()

    def get_latest_by_motor_id(self, motor_id: UUID) -> PredictionHistory | None:
        statement = (
            select(PredictionHistory)
            .where(PredictionHistory.motor_id == motor_id)
            .order_by(desc(PredictionHistory.predicted_at))
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def get_risk_history(
        self,
        motor_id: UUID,
        days: int = 30,
    ) -> Sequence[PredictionHistory]:
        since = datetime.now(UTC) - timedelta(days=days)
        statement = (
            select(PredictionHistory)
            .where(
                PredictionHistory.motor_id == motor_id,
                PredictionHistory.predicted_at >= since,
            )
            .order_by(desc(PredictionHistory.predicted_at))
        )
        return self.db.scalars(statement).all()

    def count_by_motor_id(self, motor_id: UUID) -> int:
        result = self.db.scalar(
            select(func.count(PredictionHistory.id)).where(
                PredictionHistory.motor_id == motor_id
            )
        )
        return int(result or 0)
