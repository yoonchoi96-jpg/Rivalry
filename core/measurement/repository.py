from __future__ import annotations
from typing import Protocol
from .models import Measurement

class MeasurementRepository(Protocol):
    def save(self, measurement: Measurement) -> Measurement: ...
    def get(self, measurement_id: str) -> Measurement | None: ...

class InMemoryMeasurementRepository:
    def __init__(self) -> None: self._items: dict[str, Measurement] = {}
    def save(self, measurement: Measurement) -> Measurement:
        self._items[measurement.id] = Measurement.model_validate(measurement.model_dump(mode="json"))
        return Measurement.model_validate(self._items[measurement.id].model_dump(mode="json"))
    def get(self, measurement_id: str) -> Measurement | None:
        item=self._items.get(measurement_id)
        return None if item is None else Measurement.model_validate(item.model_dump(mode="json"))
