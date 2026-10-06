from core.decision.models import DecisionPolicy, DecisionPolicyRule
from core.decision.recommendation_repository import InMemoryDecisionRecommendationRepository
from core.decision.registry import DecisionPolicyRegistry
from core.impact.models import BusinessImpact
from core.impact.repository import InMemoryImpactRepository
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType
from core.signal.models import Signal, SignalDirection, SignalKind
from core.signal.repository import InMemorySignalRepository


def make_signal() -> Signal:
    return Signal(
        id="s-job",
        entity_id="e-job",
        definition_key="competitive_price_pressure",
        signal_kind=SignalKind.CHANGE,
        direction=SignalDirection.UP,
        current_value=0.2,
        reference_value=0.1,
        delta=0.1,
        delta_pct=1.0,
        detected_at="2026-10-06T00:00:00Z",
        observation_ids=["o-job"],
        measurement_ids=["m-job"],
        confidence=0.9,
        significance=0.8,
        knowledge_kind="fact",
        rationale="change detected",
        freshness_minutes=60,
    )


def make_impact() -> BusinessImpact:
    return BusinessImpact(
        id="i-job",
        business_id="b-job",
        entity_id="e-job",
        signal_id="s-job",
        factor_key="competitive_price",
        exposure=1.0,
        magnitude=0.5,
        confidence=0.8,
        significance=0.8,
        observation_ids=["o-job"],
        measurement_ids=["m-job"],
    )


def make_handlers():
    signals = InMemorySignalRepository()
    signals.save(make_signal())
    impacts = InMemoryImpactRepository()
    impacts.save(make_impact())
    policies = DecisionPolicyRegistry()
    policies.register(
        "policy-job-v1",
        DecisionPolicy(
            name="job",
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
    recommendations = InMemoryDecisionRecommendationRepository()
    handlers = JobHandlers(
        impact_repository=impacts,
        decision_policies=policies,
        decision_recommendations=recommendations,
        signal_repository=signals,
    )
    return handlers, recommendations


def test_generate_decision_job_persists_recommendation():
    handlers, recommendations = make_handlers()

    result = handlers.generate_decision(
        Job(
            type=JobType.GENERATE_DECISION,
            payload={"impact_id": "i-job", "policy_id": "policy-job-v1"},
        )
    )

    stored = recommendations.get("i-job")
    assert stored is not None
    assert result["recommendation"]["action"] == "review"
    assert stored.policy_id == "policy-job-v1"
    assert stored.signal_id == "s-job"


def test_generate_decision_requires_existing_policy():
    handlers, _ = make_handlers()

    try:
        handlers.generate_decision(
            Job(
                type=JobType.GENERATE_DECISION,
                payload={"impact_id": "i-job", "policy_id": "missing"},
            )
        )
    except ValueError as exc:
        assert "decision policy not found" in str(exc)
    else:
        raise AssertionError("missing policy must fail")


def test_dispatch_action_persists_recommendation_alert():
    handlers, _ = make_handlers()
    generated = handlers.generate_decision(
        Job(
            type=JobType.GENERATE_DECISION,
            payload={"impact_id": "i-job", "policy_id": "policy-job-v1"},
        )
    )

    result = handlers.dispatch_action(
        Job(
            type=JobType.DISPATCH_ACTION,
            payload={"recommendation": generated["recommendation"]},
        )
    )

    assert result["action"]["kind"] == "alert"
    assert result["alert"]["type"] == "DECISION_RECOMMENDATION"
    assert result["alert"]["recommendation_id"] == "i-job"
    assert handlers.store.alerts[-1]["recommended_action"] == "review"
    assert handlers.store.alerts[-1]["impact_score"] == 50.0
    assert handlers.store.alerts[-1]["follow_up_job"] is None
