from __future__ import annotations

from core.decision.models import DecisionRecommendation

from .models import ActionKind, RecommendationAction


class ActionDispatcher:
    """Translate a recommendation into a safe, deterministic follow-up action.

    Rivalry remains recommend-only: action dispatch creates internal jobs/alerts,
    never external business-side mutations.
    """

    def dispatch(self, recommendation: DecisionRecommendation) -> RecommendationAction:
        normalized = recommendation.action.strip().lower()
        kind = (
            ActionKind.RESEARCH
            if any(token in normalized for token in ("research", "investigate", "verify", "review"))
            else ActionKind.ALERT
        )
        return RecommendationAction(
            recommendation_id=recommendation.impact_id,
            business_id=recommendation.business_id,
            action=recommendation.action,
            kind=kind,
            priority=recommendation.priority,
            rationale=recommendation.rationale,
            confidence=recommendation.confidence,
            impact_id=recommendation.impact_id,
            signal_id=recommendation.signal_id,
            factor_key=recommendation.factor_key,
            policy_id=recommendation.policy_id,
        )
