from __future__ import annotations

from typing import Protocol

from .entity import BusinessEntity


class BusinessRepository(Protocol):
    def save(self, business: BusinessEntity) -> BusinessEntity: ...
    def get(self, business_id: str) -> BusinessEntity | None: ...


class InMemoryBusinessRepository:
    def __init__(self) -> None:
        self._items: dict[str, BusinessEntity] = {}

    def save(self, business: BusinessEntity) -> BusinessEntity:
        value = BusinessEntity.model_validate(business.model_dump(mode="json"))
        self._items[value.id] = value
        return BusinessEntity.model_validate(value.model_dump(mode="json"))

    def get(self, business_id: str) -> BusinessEntity | None:
        value = self._items.get(business_id)
        return BusinessEntity.model_validate(value.model_dump(mode="json")) if value else None
