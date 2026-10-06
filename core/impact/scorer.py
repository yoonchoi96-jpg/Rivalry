from __future__ import annotations

from core.signal.models import Signal
from .models import BusinessImpact


def score_impact(impact: BusinessImpact) -> float:
    return max(0.0, min(1.0, abs(impact.magnitude) * impact.exposure * impact.significance))


def build_business_impact(
    *,
    id: str,
    business_id: str,
    signal: Signal,
    factor_key: str,
    exposure: float,
    magnitude: float,
    rationale: str = "",
) -> BusinessImpact:
    return BusinessImpact(
        id=id,
        business_id=business_id,
        entity_id=signal.entity_id,
        signal_id=signal.id,
        factor_key=factor_key,
        exposure=exposure,
        magnitude=magnitude,
        confidence=signal.confidence,
        significance=signal.significance,
        rationale=rationale,
        observation_ids=signal.observation_ids,
        measurement_ids=signal.measurement_ids,
    )
