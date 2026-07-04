from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.sensor_data import SensorData


class SensorDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_recent(self, motor_id: UUID, limit: int = 20) -> List[SensorData]:
        result = await self.session.execute(
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(desc(SensorData.recorded_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest(self, motor_id: UUID) -> Optional[SensorData]:
        result = await self.session.execute(
            select(SensorData)
            .where(SensorData.motor_id == motor_id)
            .order_by(desc(SensorData.recorded_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_time_range(
        self,
        motor_id: UUID,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> List[SensorData]:
        conditions = [
            SensorData.motor_id == motor_id,
            SensorData.recorded_at >= since,
        ]
        if until:
            conditions.append(SensorData.recorded_at <= until)

        result = await self.session.execute(
            select(SensorData)
            .where(and_(*conditions))
            .order_by(desc(SensorData.recorded_at))
        )
        return list(result.scalars().all())

    async def create(self, record: SensorData) -> SensorData:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
