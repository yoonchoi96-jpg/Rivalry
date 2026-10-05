from __future__ import annotations

from typing import Protocol

from .models import Competitor


class CompetitorRepository(Protocol):
    def list(self) -> list[Competitor]: ...
    def add(self, competitor: Competitor) -> Competitor: ...


class InMemoryCompetitorRepository:
    def __init__(self) -> None:
        self._items: dict[str, Competitor] = {}

    def list(self) -> list[Competitor]:
        return list(self._items.values())

    def add(self, competitor: Competitor) -> Competitor:
        self._items[competitor.id] = competitor
        return competitor
