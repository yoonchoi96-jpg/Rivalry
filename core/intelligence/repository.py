from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import Change, CostSignal, Prediction, Review


class IntelligenceRepository(Protocol):
    def record_changes(self, changes: list[Change]) -> None: ...
    def record_reviews(self, reviews: list[Review]) -> None: ...
    def record_prediction(self, prediction: Prediction) -> None: ...
    def record_alert(self, alert: dict[str, object]) -> None: ...
    def record_snapshot(self, competitor_id: str, snapshot: dict[str, object]) -> None: ...
    def latest_snapshot(self, competitor_id: str) -> dict[str, object]: ...
    def record_cost_signals(self, signals: list[CostSignal]) -> None: ...
    def all_changes(self) -> list[Change]: ...
    def all_reviews(self) -> list[Review]: ...
    def all_predictions(self) -> list[Prediction]: ...
    def all_cost_signals(self) -> list[CostSignal]: ...
    def all_alerts(self) -> list[dict[str, object]]: ...


@dataclass
class InMemoryIntelligenceRepository:
    """Reference repository; replace with DB/Redis implementation without changing services."""

    changes: list[Change] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    predictions: list[Prediction] = field(default_factory=list)
    cost_signal_items: list[CostSignal] = field(default_factory=list)
    alerts: list[dict[str, object]] = field(default_factory=list)
    snapshots: dict[str, dict[str, object]] = field(default_factory=dict)

    def record_changes(self, changes: list[Change]) -> None:
        self.changes.extend(Change.model_validate(item.model_dump(mode="json")) for item in changes)

    def record_reviews(self, reviews: list[Review]) -> None:
        self.reviews.extend(Review.model_validate(item.model_dump(mode="json")) for item in reviews)

    def record_prediction(self, prediction: Prediction) -> None:
        self.predictions.append(Prediction.model_validate(prediction.model_dump(mode="json")))

    def record_alert(self, alert: dict[str, object]) -> None:
        self.alerts.append(dict(alert))

    def record_snapshot(self, competitor_id: str, snapshot: dict[str, object]) -> None:
        self.snapshots[competitor_id] = dict(snapshot)

    def latest_snapshot(self, competitor_id: str) -> dict[str, object]:
        return self.snapshots.get(competitor_id, {})

    def record_cost_signals(self, signals: list[CostSignal]) -> None:
        self.cost_signal_items.extend(
            CostSignal.model_validate(item.model_dump(mode="json")) for item in signals
        )

    def all_changes(self) -> list[Change]:
        return list(self.changes)

    def all_reviews(self) -> list[Review]:
        return list(self.reviews)

    def all_predictions(self) -> list[Prediction]:
        return list(self.predictions)

    def all_cost_signals(self) -> list[CostSignal]:
        return list(self.cost_signal_items)

    def all_alerts(self) -> list[dict[str, object]]:
        return [dict(alert) for alert in self.alerts]
