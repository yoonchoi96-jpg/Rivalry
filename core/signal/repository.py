from __future__ import annotations

from typing import Protocol

from .models import Signal


class SignalRepository(Protocol):
    def save(self, signal: Signal) -> Signal: ...
    def get(self, signal_id: str) -> Signal | None: ...


class InMemorySignalRepository:
    def __init__(self) -> None:
        self._items: dict[str, Signal] = {}

    def save(self, signal: Signal) -> Signal:
        self._items[signal.id] = Signal.model_validate(signal.model_dump(mode="json"))
        return Signal.model_validate(self._items[signal.id].model_dump(mode="json"))

    def get(self, signal_id: str) -> Signal | None:
        item = self._items.get(signal_id)
        return None if item is None else Signal.model_validate(item.model_dump(mode="json"))
