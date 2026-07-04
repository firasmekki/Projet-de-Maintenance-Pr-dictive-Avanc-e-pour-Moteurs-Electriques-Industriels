from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select

from app.db.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    def get_for_motor(self, motor_id: UUID, limit: int = 100) -> Sequence[Recommendation]:
        statement = (
            select(Recommendation)
            .where(Recommendation.motor_id == motor_id)
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
        )
        return self.db.scalars(statement).all()
