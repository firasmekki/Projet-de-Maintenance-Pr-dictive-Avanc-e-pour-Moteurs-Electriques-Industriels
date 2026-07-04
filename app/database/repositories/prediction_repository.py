from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.prediction_history import PredictionHistory


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, prediction: PredictionHistory) -> PredictionHistory:
        self.session.add(prediction)
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def get_by_motor_id(
        self,
        motor_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PredictionHistory]:
        result = await self.session.execute(
            select(PredictionHistory)
            .where(PredictionHistory.motor_id == motor_id)
            .order_by(desc(PredictionHistory.prediction_date))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_latest_by_motor_id(self, motor_id: UUID) -> Optional[PredictionHistory]:
        result = await self.session.execute(
            select(PredictionHistory)
            .where(PredictionHistory.motor_id == motor_id)
            .order_by(desc(PredictionHistory.prediction_date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_risk_history(
        self,
        motor_id: UUID,
        days: int = 30,
    ) -> List[PredictionHistory]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(PredictionHistory)
            .where(
                and_(
                    PredictionHistory.motor_id == motor_id,
                    PredictionHistory.prediction_date >= since,
                )
            )
            .order_by(desc(PredictionHistory.prediction_date))
        )
        return list(result.scalars().all())

    async def count_by_motor_id(self, motor_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(PredictionHistory)
            .where(PredictionHistory.motor_id == motor_id)
        )
        return result.scalar_one()

    async def get_by_id(self, prediction_id: UUID) -> Optional[PredictionHistory]:
        result = await self.session.execute(
            select(PredictionHistory).where(PredictionHistory.id == prediction_id)
        )
        return result.scalar_one_or_none()
