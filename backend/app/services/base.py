from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.events.bus import EventBus

ModelT = TypeVar("ModelT")
RepoT = TypeVar("RepoT", bound=BaseRepository)


class Service:
    def __init__(self, db: AsyncSession, event_bus: EventBus | None = None) -> None:
        self.db = db
        self.event_bus = event_bus

    async def _publish(self, event_type: str, payload: dict) -> None:
        if self.event_bus is None:
            return
        from app.events.types import ApexEvent

        await self.event_bus.publish(ApexEvent(type=event_type, payload=payload))


class RepositoryService(Service, Generic[ModelT, RepoT]):
    def __init__(self, db: AsyncSession, repository: RepoT, event_bus: EventBus | None = None) -> None:
        super().__init__(db, event_bus)
        self.repository = repository
