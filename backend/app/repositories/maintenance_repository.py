from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select

from app.db.models.maintenance_history import MaintenanceHistory
from app.repositories.base import BaseRepository


class MaintenanceRepository(BaseRepository[MaintenanceHistory]):
    model = MaintenanceHistory

    def get_for_motor(self, motor_id: UUID, limit: int = 100) -> Sequence[MaintenanceHistory]:
        statement = (
            select(MaintenanceHistory)
            .where(MaintenanceHistory.motor_id == motor_id)
            .order_by(desc(MaintenanceHistory.performed_at))
            .limit(limit)
        )
        return self.db.scalars(statement).all()
