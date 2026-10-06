import pytest

from core.decision.engine import DecisionEngine
from core.decision.models import DecisionPolicy, DecisionPolicyRule
from core.impact.models import BusinessImpact
from core.signal.models import Signal, SignalDirection, SignalKind


def make_signal() -> Signal:
    return Signal(
        id="s1",
        entity_id="e1",
        definition_key="competitive_price_pressure",
        signal_kind=SignalKind.CHANGE,
        direction=SignalDirection.UP,
        current_value=0.2,
        reference_value=0.1,
        delta=0.1,
        delta_pct=1.0,
        detected_at="2026-10-06T00:00:00Z",
        observation_ids=["o1"],
        measurement_ids=["m1"],
        confidence=0.9,
        significance=0.8,
        knowledge_kind="fact",
        rationale="change detected",
        freshness_minutes=60,
    )


def make_impact() -> BusinessImpact:
    return BusinessImpact(
        id="i1",
        business_id="b1",
        entity_id="e1",
        signal_id="s1",
        factor_key="competitive_price",
        exposure=1.0,
        magnitude=0.5,
        confidence=0.8,
        significance=0.8,
        observation_ids=["o1"],
        measurement_ids=["m1"],
    )


def test_decision_engine_uses_declarative_policy_and_preserves_lineage():
    recommendation = DecisionEngine().recommend(
        make_impact(),
        make_signal(),
        DecisionPolicy(
            id="test-v1",
            name="test",
            default_action="monitor",
            default_rationale="keep observing",
            rules=[
                DecisionPolicyRule(
                    factor_key="competitive_price",
                    min_impact=0.2,
                    max_impact=1.0,
                    action="review",
                    rationale="material impact requires review",
                )
            ],
        ),
    )

    assert recommendation.action == "review"
    assert recommendation.business_id == "b1"
    assert recommendation.impact_id == "i1"
    assert recommendation.signal_id == "s1"
    assert recommendation.factor_key == "competitive_price"
    assert recommendation.priority > 0
    assert recommendation.policy_id == "test-v1"


def test_decision_engine_rejects_broken_lineage():
    impact = make_impact()
    impact.measurement_ids = ["wrong"]
    with pytest.raises(ValueError, match="measurement lineage"):
        DecisionEngine().recommend(
            impact,
            make_signal(),
            DecisionPolicy(
                id="test-v1",
                name="test",
                default_action="monitor",
                default_rationale="keep observing",
            ),
        )
