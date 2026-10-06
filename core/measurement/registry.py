from __future__ import annotations

from .models import MeasurementDefinition


class MeasurementRegistry:
    """Declarative registry for reusable business measurements."""

    def __init__(self, definitions: list[MeasurementDefinition] | None = None) -> None:
        self._definitions = {item.key: item for item in (definitions or [])}

    def register(self, definition: MeasurementDefinition) -> None:
        self._definitions[definition.key] = definition

    def get(self, key: str) -> MeasurementDefinition | None:
        return self._definitions.get(key)

    def all(self) -> list[MeasurementDefinition]:
        return list(self._definitions.values())


DEFAULT_MEASUREMENTS = [
    MeasurementDefinition(
        key="competitive_price_pressure",
        required_entities=["competitor_product"],
        input_metrics=["price"],
        formula="normalized_current_price / normalized_reference_price - 1",
        unit="ratio",
        time_window="current_vs_reference",
        freshness_minutes=60,
        quality_rules=["same_currency", "comparable_product", "minimum_sample_size"],
    ),
    MeasurementDefinition(
        key="fx_exposure",
        required_entities=["business", "currency_pair"],
        input_metrics=["fx_rate"],
        formula="current_fx_rate / reference_fx_rate - 1",
        unit="ratio",
        time_window="current_vs_reference",
        freshness_minutes=60,
        quality_rules=["currency_pair_matches_business_exposure"],
    ),
]
