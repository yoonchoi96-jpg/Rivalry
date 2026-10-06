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


def test_research_action_builds_executable_follow_up_plan():
    action = ActionDispatcher().dispatch(make_recommendation("investigate"))
    assert action.kind == ActionKind.RESEARCH
    assert action.follow_up_job.value == "execute_research"
    plan = action.follow_up_payload["plan"]
    assert plan["tasks"][0]["factor_key"] == "competitive_price"
    assert plan["tasks"][0]["method"] == "web"\n    assert plan["tasks"][0]["priority"] == 80


def test_unknown_action_defaults_to_safe_alert():
    action = ActionDispatcher().dispatch(make_recommendation("change_packaging"))
    assert action.kind == ActionKind.ALERT
    assert action.follow_up_job is None
