from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Change, CostSignal, Prediction, Review
from .repository import InMemoryIntelligenceRepository, IntelligenceRepository
from .services import AlertIntelligenceService, ReviewIntelligenceService


def _parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class IntelligenceStore:
    """Application-facing intelligence facade backed by an injectable repository."""

    def __init__(
        self,
        repository: IntelligenceRepository | None = None,
        *,
        changes: list[Change] | None = None,
        reviews: list[Review] | None = None,
        predictions: list[Prediction] | None = None,
        cost_signal_items: list[CostSignal] | None = None,
        alerts: list[dict[str, object]] | None = None,
    ) -> None:
        repo = repository or InMemoryIntelligenceRepository()
        self.repository = repo
        if changes:
            repo.record_changes(changes)
        if reviews:
            repo.record_reviews(reviews)
        if predictions:
            for prediction in predictions:
                repo.record_prediction(prediction)
        if cost_signal_items:
            repo.cost_signal_items.extend(cost_signal_items)
        if alerts:
            for alert in alerts:
                repo.record_alert(alert)

    @property
    def changes(self) -> list[Change]:
        return self.repository.all_changes()

    @property
    def reviews(self) -> list[Review]:
        return self.repository.all_reviews()

    @property
    def predictions(self) -> list[Prediction]:
        return self.repository.all_predictions()

    @property
    def cost_signal_items(self) -> list[CostSignal]:
        return self.repository.all_cost_signals()

    @property
    def alerts(self) -> list[dict[str, object]]:
        return self.repository.all_alerts()

    def record_changes(self, changes: list[Change]) -> None:
        self.repository.record_changes(changes)

    def record_reviews(self, reviews: list[Review]) -> None:
        self.repository.record_reviews(reviews)

    def record_prediction(self, prediction: Prediction) -> None:
        self.repository.record_prediction(prediction)

    def record_alert(self, alert: dict[str, object]) -> None:
        self.repository.record_alert(alert)

    def _recent(self, values, field_name: str, days: int):
        if days <= 0:
            return list(values)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = []
        for value in values:
            parsed = _parse_time(getattr(value, field_name))
            if parsed is None or parsed >= cutoff:
                result.append(value)
        return result

    def today_changes(self, business_id: str, days: int = 1) -> list[Change]:
        values = [
            c for c in self._recent(self.changes, "detected_at", days)
            if c.business_id in (None, business_id)
        ]
        return AlertIntelligenceService.prioritize(values, 10)

    def latest_snapshot(self, competitor_id: str) -> dict[str, object]:
        return self.repository.latest_snapshot(competitor_id)

    def record_snapshot(self, competitor_id: str, snapshot: dict[str, object]) -> None:
        self.repository.record_snapshot(competitor_id, snapshot)

    def competitor_history(self, competitor_id: str, days: int = 30) -> list[Change]:
        values = [
            c for c in self._recent(self.changes, "detected_at", days)
            if c.competitor_id == competitor_id
        ]
        return sorted(values, key=lambda c: c.detected_at, reverse=True)

    def review_trends(self, competitor_id: str, days: int = 30) -> dict[str, object]:
        values = [
            r for r in self._recent(self.reviews, "created_at", days)
            if r.competitor_id == competitor_id
        ]
        return ReviewIntelligenceService.summarize(values)

    def cost_signals(self, product_id: str, days: int = 30) -> list[dict[str, object]]:
        values = [
            s for s in self._recent(self.cost_signal_items, "observed_at", days)
            if s.product_id == product_id
        ]
        return [s.model_dump() for s in values]

    def rival_profile(self, competitor_id: str) -> dict[str, object]:
        history = self.competitor_history(competitor_id)
        reviews = self.review_trends(competitor_id)
        counts: dict[str, int] = {}
        for change in history:
            counts[change.type] = counts.get(change.type, 0) + 1
        return {
            "competitor_id": competitor_id,
            "change_count": len(history),
            "change_types": counts,
            "recent_changes": [c.model_dump() for c in history[:10]],
            "review_health": reviews,
        }

    def market_pulse(self, business_id: str, days: int = 7) -> dict[str, object]:
        changes = self.today_changes(business_id, days)
        type_counts: dict[str, int] = {}
        for change in changes:
            type_counts[change.type] = type_counts.get(change.type, 0) + 1
        return {
            "business_id": business_id,
            "days": days,
            "change_count": len(changes),
            "change_types": type_counts,
            "top_changes": [c.model_dump() for c in changes],
        }

    def predictions_for(self, competitor_id: str) -> list[Prediction]:
        return [p for p in self.predictions if p.competitor_id == competitor_id]

    def alerts_for(self, competitor_id: str) -> list[dict[str, object]]:
        return [a for a in self.alerts if str(a.get("competitor_id", "")) == competitor_id]

    def research_context(self, business_id: str | None = None, competitor_id: str | None = None) -> dict[str, object]:
        result: dict[str, object] = {}
        if business_id:
            result["market_pulse"] = self.market_pulse(business_id, 7)
            result["today_changes"] = [c.model_dump() for c in self.today_changes(business_id, 1)]
        if competitor_id:
            result["rival_profile"] = self.rival_profile(competitor_id)
            result["review_trends"] = self.review_trends(competitor_id, 30)
            result["predictions"] = [p.model_dump() for p in self.predictions_for(competitor_id)]
            result["alerts"] = self.alerts_for(competitor_id)
        return result
