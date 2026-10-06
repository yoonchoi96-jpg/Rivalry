from __future__ import annotations

from typing import Protocol

from .models import SourceProfile


class SourceRepository(Protocol):
    def save(self, source: SourceProfile) -> SourceProfile: ...
    def get(self, source_id: str) -> SourceProfile | None: ...
    def list(self) -> list[SourceProfile]: ...


class InMemorySourceRepository:
    def __init__(self) -> None:
        self._items: dict[str, SourceProfile] = {}

    def save(self, source: SourceProfile) -> SourceProfile:
        self._items[source.id] = SourceProfile.model_validate(source.model_dump())
        return SourceProfile.model_validate(source.model_dump())

    def get(self, source_id: str) -> SourceProfile | None:
        item = self._items.get(source_id)
        return None if item is None else SourceProfile.model_validate(item.model_dump())

    def list(self) -> list[SourceProfile]:
        return [SourceProfile.model_validate(item.model_dump()) for item in self._items.values()]
