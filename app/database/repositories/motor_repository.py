from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.motor import Motor


class MotorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, motor_id: UUID) -> Optional[Motor]:
        result = await self.session.execute(
            select(Motor).where(Motor.id == motor_id, Motor.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Motor]:
        result = await self.session.execute(
            select(Motor)
            .where(Motor.is_active.is_(True))
            .order_by(Motor.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, motor: Motor) -> Motor:
        self.session.add(motor)
        await self.session.commit()
        await self.session.refresh(motor)
        return motor

    async def exists(self, motor_id: UUID) -> bool:
        result = await self.session.execute(
            select(Motor.id).where(Motor.id == motor_id)
        )
        return result.scalar_one_or_none() is not None
