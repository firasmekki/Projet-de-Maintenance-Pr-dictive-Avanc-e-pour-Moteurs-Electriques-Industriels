from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select

from app.db.models.fault_history import FaultHistory
from app.repositories.base import BaseRepository


class FaultRepository(BaseRepository[FaultHistory]):
    model = FaultHistory

    def get_for_motor(self, motor_id: UUID, limit: int = 100) -> Sequence[FaultHistory]:
        statement = (
            select(FaultHistory)
            .where(FaultHistory.motor_id == motor_id)
            .order_by(desc(FaultHistory.detected_at))
            .limit(limit)
        )
        return self.db.scalars(statement).all()

    def get_latest_for_motor(self, motor_id: UUID) -> FaultHistory | None:
        statement = (
            select(FaultHistory)
            .where(FaultHistory.motor_id == motor_id)
            .order_by(desc(FaultHistory.detected_at))
            .limit(1)
        )
        return self.db.scalars(statement).first()
