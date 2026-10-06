from core.action.dispatcher import ActionDispatcher
from core.action.models import ActionKind
from core.decision.models import DecisionRecommendation


def make_recommendation(action: str) -> DecisionRecommendation:
    return DecisionRecommendation(
        business_id="b1",
        impact_id="i1",
        action=action,
        priority=.8,
        rationale="material impact",
        confidence=.9,
        signal_id="s1",
        factor_key="competitive_price",
        policy_id="policy-v1",
    )


def test_recommendation_dispatches_research_actions_to_research():
    action = ActionDispatcher().dispatch(make_recommendation("investigate_competitor_pricing"))
    assert action.kind == ActionKind.RESEARCH
    assert action.recommendation_id == "i1"


def test_recommendation_dispatches_other_actions_to_alert():
    action = ActionDispatcher().dispatch(make_recommendation("monitor_before_matching_price"))
    assert action.kind == ActionKind.ALERT
