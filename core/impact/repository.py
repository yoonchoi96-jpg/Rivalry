from __future__ import annotations

from typing import Protocol

from .models import BusinessImpact


class ImpactRepository(Protocol):
    def save(self, impact: BusinessImpact) -> BusinessImpact: ...
    def get(self, impact_id: str) -> BusinessImpact | None: ...


class InMemoryImpactRepository:
    def __init__(self) -> None:
        self._items: dict[str, BusinessImpact] = {}

    def save(self, impact: BusinessImpact) -> BusinessImpact:
        self._items[impact.id] = BusinessImpact.model_validate(impact.model_dump(mode="json"))
        return BusinessImpact.model_validate(self._items[impact.id].model_dump(mode="json"))

    def get(self, impact_id: str) -> BusinessImpact | None:
        item = self._items.get(impact_id)
        return None if item is None else BusinessImpact.model_validate(item.model_dump(mode="json"))
