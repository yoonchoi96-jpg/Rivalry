from __future__ import annotations

from core.impact.models import BusinessImpact
from core.impact.scorer import score_impact
from .models import RelevanceProfile, RelevanceScore, rank_relevance


def score_impact_relevance(
    impact: BusinessImpact,
    profile: RelevanceProfile | None = None,
) -> RelevanceScore:
    relevance = 0.5
    if profile:
        relevance = profile.factor_weights.get(impact.factor_key, relevance)
    impact_score = score_impact(impact)
    priority = rank_relevance(relevance=relevance, impact=impact_score, confidence=impact.confidence)
    return RelevanceScore(
        business_id=impact.business_id,
        item_id=impact.id,
        relevance=relevance,
        impact=impact_score,
        confidence=impact.confidence,
        priority=priority,
    )
