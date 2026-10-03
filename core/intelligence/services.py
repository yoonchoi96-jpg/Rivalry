from __future__ import annotations

from collections import Counter
from math import prod
from typing import Iterable

from .models import Change, Review


class ImpactScoringService:
    """Deterministic scoring primitives that can later consume learned weights."""

    @staticmethod
    def score(
        magnitude: float,
        frequency: float,
        market_relevance: float,
        competitor_importance: float,
        persistence: float,
    ) -> float:
        values = [
            max(0.0, min(100.0, float(value)))
            for value in (
                magnitude,
                frequency,
                market_relevance,
                competitor_importance,
                persistence,
            )
        ]
        return round(prod(values) ** (1 / len(values)), 2)

    @classmethod
    def apply(
        cls,
        change: Change,
        *,
        frequency: float = 0,
        market_relevance: float = 0,
        competitor_importance: float = 0,
        persistence: float = 0,
    ) -> Change:
        score = cls.score(
            change.magnitude,
            frequency,
            market_relevance,
            competitor_importance,
            persistence,
        )
        return change.model_copy(update={"impact_score": score})


class ReviewIntelligenceService:
    @staticmethod
    def summarize(reviews: Iterable[Review]) -> dict[str, object]:
        items = list(reviews)
        positive = sum(r.sentiment == "positive" for r in items)
        negative = sum(r.sentiment == "negative" for r in items)
        neutral = sum(r.sentiment == "neutral" for r in items)
        ratings = [r.rating for r in items if r.rating is not None]
        topics = Counter(topic for review in items for topic in review.topics)
        return {
            "review_count": len(items),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "top_topics": [{"topic": topic, "count": count} for topic, count in topics.most_common(10)],
        }


class AlertIntelligenceService:
    """Turns raw changes into compact intelligence records for downstream AI."""

    @staticmethod
    def prioritize(changes: Iterable[Change], limit: int = 10) -> list[Change]:
        return sorted(
            changes,
            key=lambda item: (item.impact_score, item.confidence),
            reverse=True,
        )[:max(1, limit)]
