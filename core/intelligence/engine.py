from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import Change, Prediction, Review
from .services import AlertIntelligenceService, ReviewIntelligenceService


@dataclass
class IntelligenceStore:
    """Small application-facing store contract.

    Real persistence can implement this interface later without changing AI tools.
    """

    changes: list[Change] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    predictions: list[Prediction] = field(default_factory=list)

    def today_changes(self, business_id: str, days: int = 1) -> list[Change]:
        return AlertIntelligenceService.prioritize(self.changes, 10)

    def competitor_history(self, competitor_id: str, days: int = 30) -> list[Change]:
        return [c for c in self.changes if c.competitor_id == competitor_id]

    def review_trends(self, competitor_id: str, days: int = 30) -> dict[str, object]:
        return ReviewIntelligenceService.summarize(
            r for r in self.reviews if r.competitor_id == competitor_id
        )

    def cost_signals(self, product_id: str, days: int = 30) -> list[dict[str, object]]:
        return []

    def rival_profile(self, competitor_id: str) -> dict[str, object]:
        history = self.competitor_history(competitor_id)
        reviews = self.review_trends(competitor_id)
        return {
            "competitor_id": competitor_id,
            "change_count": len(history),
            "recent_changes": [c.model_dump() for c in history[:10]],
            "review_health": reviews,
        }

    def market_pulse(self, business_id: str, days: int = 7) -> dict[str, object]:
        changes = self.today_changes(business_id, days)
        return {
            "business_id": business_id,
            "days": days,
            "change_count": len(changes),
            "top_changes": [c.model_dump() for c in changes],
        }

    def predictions_for(self, competitor_id: str) -> list[Prediction]:
        return [p for p in self.predictions if p.competitor_id == competitor_id]
