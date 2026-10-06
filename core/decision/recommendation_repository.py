from __future__ import annotations

from typing import Protocol

from .models import DecisionRecommendation


class DecisionRecommendationRepository(Protocol):
    def save(self, recommendation: DecisionRecommendation) -> DecisionRecommendation: ...
    def get(self, recommendation_id: str) -> DecisionRecommendation | None: ...
    def list_for_business(self, business_id: str) -> list[DecisionRecommendation]: ...


class InMemoryDecisionRecommendationRepository:
    def __init__(self) -> None:
        self._items: dict[str, DecisionRecommendation] = {}

    def save(self, recommendation: DecisionRecommendation) -> DecisionRecommendation:
        stored = DecisionRecommendation.model_validate(
            recommendation.model_dump(mode="json")
        )
        self._items[stored.impact_id] = stored
        return DecisionRecommendation.model_validate(stored.model_dump(mode="json"))

    def get(self, recommendation_id: str) -> DecisionRecommendation | None:
        item = self._items.get(recommendation_id)
        return None if item is None else DecisionRecommendation.model_validate(
            item.model_dump(mode="json")
        )

    def list_for_business(self, business_id: str) -> list[DecisionRecommendation]:
        return [
            DecisionRecommendation.model_validate(item.model_dump(mode="json"))
            for item in self._items.values()
            if item.business_id == business_id
        ]
