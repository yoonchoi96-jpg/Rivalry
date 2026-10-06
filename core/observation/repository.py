from __future__ import annotations

from typing import Protocol

from .models import Observation


class ObservationRepository(Protocol):
    def save(self, observation: Observation) -> Observation: ...
    def get(self, observation_id: str) -> Observation | None: ...


class InMemoryObservationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Observation] = {}

    def save(self, observation: Observation) -> Observation:
        self._items[observation.id] = Observation.model_validate(observation.model_dump(mode="json"))
        return Observation.model_validate(self._items[observation.id])

    def get(self, observation_id: str) -> Observation | None:
        item = self._items.get(observation_id)
        return None if item is None else Observation.model_validate(item.model_dump(mode="json"))
