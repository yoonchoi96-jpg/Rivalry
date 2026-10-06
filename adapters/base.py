from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PlatformAdapter(ABC):
    @abstractmethod
    def discover_competitors(self, business: dict[str, object]) -> list[dict[str, object]]: ...

    @abstractmethod
    def get_products(self, competitor: dict[str, object]) -> list[dict[str, object]]: ...

    @abstractmethod
    def get_prices(self, competitor: dict[str, object]) -> list[object]: ...

    @abstractmethod
    def get_reviews(self, competitor: dict[str, object]) -> list[object]: ...

    @abstractmethod
    def get_promotions(self, competitor: dict[str, object]) -> list[object]: ...

    def research(self, task: Any, source: Any) -> dict[str, Any]:
        raise NotImplementedError("adapter does not implement research")
