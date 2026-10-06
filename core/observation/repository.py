from __future__ import annotations

from typing import Protocol

from .models import Observation


class ObservationRepository(Protocol):
    def save(self, observation: Observation) -> Observation: ...
    def get(self, observation_id: str) -> Observation | None: ...
    def latest_for_entity_metric(self, entity_id: str, metric: str, *, exclude_id: str | None = None) -> Observation | None: ...


class InMemoryObservationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Observation] = {}

    def save(self, observation: Observation) -> Observation:
        self._items[observation.id] = Observation.model_validate(observation.model_dump(mode="json"))
        return Observation.model_validate(self._items[observation.id])

    def get(self, observation_id: str) -> Observation | None:
        item = self._items.get(observation_id)
        return None if item is None else Observation.model_validate(item.model_dump(mode="json"))

    def latest_for_entity_metric(self, entity_id: str, metric: str, *, exclude_id: str | None = None) -> Observation | None:
        candidates = [x for x in self._items.values() if x.entity_id == entity_id and x.metric == metric and x.id != exclude_id]
        if not candidates:
            return None
        return Observation.model_validate(max(candidates, key=lambda x: x.observed_at).model_dump(mode="json"))

    def latest_for_entity_metric(self, entity_id: str, metric: str, *, exclude_id: str | None = None) -> Observation | None:
        candidates = [item for item in self._items.values() if item.entity_id == entity_id and item.metric == metric and item.id != exclude_id]
        if not candidates:
            return None
        return Observation.model_validate(max(candidates, key=lambda item: item.observed_at).model_dump(mode="json"))
