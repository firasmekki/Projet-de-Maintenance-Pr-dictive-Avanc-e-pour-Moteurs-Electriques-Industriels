from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict[str, Any]) -> ModelT:
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: UUID) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelT]:
        statement: Select[tuple[ModelT]] = select(self.model).offset(skip).limit(limit)
        return self.db.scalars(statement).all()

    def update(self, entity_id: UUID, data: dict[str, Any]) -> ModelT | None:
        entity = self.get_by_id(entity_id)
        if entity is None:
            return None

        for field, value in data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: UUID) -> bool:
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False

        self.db.delete(entity)
        self.db.commit()
        return True
