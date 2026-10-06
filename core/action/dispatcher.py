from __future__ import annotations

from core.decision.models import DecisionRecommendation
from core.jobs.models import JobType
from core.research.models import ResearchMethod, ResearchPlan, ResearchTask

from .models import ActionKind, RecommendationAction
from .registry import ActionRegistry


class ActionDispatcher:
    """Translate a recommendation into a safe, deterministic follow-up action.

    Rivalry remains recommend-only: action dispatch creates internal jobs/alerts,
    never external business-side mutations.
    """

    def __init__(self, registry: ActionRegistry | None = None) -> None:
        self.registry = registry or ActionRegistry()

    def dispatch(self, recommendation: DecisionRecommendation) -> RecommendationAction:
        definition = self.registry.resolve(recommendation.action)
        kind = ActionKind.RESEARCH if definition.route.value == ActionKind.RESEARCH else ActionKind.ALERT
        follow_up_payload = None
        if definition.follow_up_job == JobType.EXECUTE_RESEARCH:
            plan = ResearchPlan(
                question=recommendation.rationale,
                tasks=[
                    ResearchTask(
                        factor_key=recommendation.factor_key,
                        objective=f"검증: {recommendation.rationale}",
                        method=ResearchMethod.WEB,
                        priority=recommendation.priority,
                        freshness_minutes=1440,
                    )
                ],
            )
            follow_up_payload = {"plan": plan.model_dump(mode="json"), "business_id": recommendation.business_id, "policy_id": recommendation.policy_id, "exposure": 0.5}

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
            follow_up_job=definition.follow_up_job,
            follow_up_payload=follow_up_payload,
        )
