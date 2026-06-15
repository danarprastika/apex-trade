from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get(self, entity_id: Any) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def get_or_raise(self, entity_id: Any, message: str) -> ModelT:
        entity = self.get(entity_id)
        if entity is None:
            raise ValueError(message)
        return entity

    def find_one(self, **filters: Any) -> ModelT | None:
        statement = select(self.model)
        for key, value in filters.items():
            statement = statement.where(getattr(self.model, key) == value)
        return self.db.scalar(statement)

    def find_many(self, **filters: Any) -> list[ModelT]:
        statement = select(self.model)
        for key, value in filters.items():
            statement = statement.where(getattr(self.model, key) == value)
        return list(self.db.scalars(statement).all())

    def list(self, limit: int = 100, offset: int = 0, order_by: Any | None = None) -> list[ModelT]:
        statement: Select[tuple[ModelT]] = select(self.model)
        if order_by is not None:
            statement = statement.order_by(order_by)
        return list(self.db.scalars(statement.limit(limit).offset(offset)).all())

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        return entity

    def add_all(self, entities: Iterable[ModelT]) -> list[ModelT]:
        entity_list = list(entities)
        self.db.add_all(entity_list)
        return entity_list

    def create(self, **kwargs: Any) -> ModelT:
        entity = self.model(**kwargs)
        return self.add(entity)

    def update(self, entity: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.db.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, entity: ModelT) -> ModelT:
        self.db.refresh(entity)
        return entity
