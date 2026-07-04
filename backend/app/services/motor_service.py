from collections.abc import Sequence
from uuid import UUID

from app.db.models.motor import Motor
from app.repositories.motor_repository import MotorRepository


class MotorService:
    def __init__(self, motor_repository: MotorRepository) -> None:
        self.motor_repository = motor_repository

    def list_motors(self, skip: int = 0, limit: int = 100) -> Sequence[Motor]:
        return self.motor_repository.get_all(skip=skip, limit=limit)

    def get_motor(self, motor_id: UUID) -> Motor | None:
        return self.motor_repository.get_by_id(motor_id)

    def get_motor_with_stats(self, motor_id: UUID) -> dict[str, object] | None:
        return self.motor_repository.get_motor_with_stats(motor_id)
