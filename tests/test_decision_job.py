from core.decision.models import DecisionPolicy, DecisionPolicyRule
from core.decision.recommendation_repository import InMemoryDecisionRecommendationRepository
from core.decision.registry import DecisionPolicyRegistry
from core.impact.models import BusinessImpact
from core.impact.repository import InMemoryImpactRepository
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType
from core.observation.repository import InMemoryObservationRepository
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


def test_dispatch_action_is_idempotent_for_same_recommendation_revision():
    handlers, _ = make_handlers()
    generated = handlers.generate_decision(
        Job(type=JobType.GENERATE_DECISION, payload={"impact_id": "i-job", "policy_id": "policy-job-v1"})
    )
    action_job = Job(
        type=JobType.DISPATCH_ACTION,
        payload={"recommendation": generated["recommendation"]},
    )
    handlers.dispatch_action(action_job)
    handlers.dispatch_action(action_job)
    assert len(handlers.store.alerts) == 1


def test_dispatch_action_alert_identity_preserves_action_revision():
    handlers, _ = make_handlers()
    generated = handlers.generate_decision(
        Job(
            type=JobType.GENERATE_DECISION,
            payload={"impact_id": "i-job", "policy_id": "policy-job-v1"},
        )
    )
    handlers.dispatch_action(
        Job(
            type=JobType.DISPATCH_ACTION,
            payload={"recommendation": generated["recommendation"]},
        )
    )

    revised = dict(generated["recommendation"])
    revised["action"] = "monitor"
    handlers.dispatch_action(
        Job(
            type=JobType.DISPATCH_ACTION,
            payload={"recommendation": revised},
        )
    )

    alerts = handlers.store.alerts
    assert len(alerts) == 2
    assert alerts[0]["id"] != alerts[1]["id"]
    assert alerts[0]["recommended_action"] == "review"
    assert alerts[1]["recommended_action"] == "monitor"


def test_worker_runs_research_to_decision_to_alert_loop():
    from core.measurement.repository import InMemoryMeasurementRepository

    observations = InMemoryObservationRepository()
    measurements = InMemoryMeasurementRepository()
    signals = InMemorySignalRepository()
    impacts = InMemoryImpactRepository()
    policies = DecisionPolicyRegistry()
    policies.register(
        "policy-loop-v1",
        DecisionPolicy(
            name="loop",
            default_action="monitor",
            default_rationale="monitor after verification",
            rules=[
                DecisionPolicyRule(
                    factor_key="competitive_price",
                    min_impact=0.005,
                    max_impact=1.0,
                    action="review",
                    rationale="verified price movement requires review",
                )
            ],
        ),
    )
    handlers = JobHandlers(
        impact_repository=impacts,
        decision_policies=policies,
        decision_recommendations=InMemoryDecisionRecommendationRepository(),
        signal_repository=signals,
        observation_repository=observations,
        measurement_repository=measurements,
    )
    handlers.ingest_research(Job(
        type=JobType.INGEST_RESEARCH,
        payload={"business_id": "b-loop", "research": {"question": "seed", "tasks": [{
            "factor_key": "competitive_price",
            "evidence": {"id": "seed-price", "captured_at": "2026-10-06T00:00:00Z",
                         "observation": {"normalized_value": 100, "unit": "KRW", "currency": "KRW"}},
        }]}},
    ))

    class FakeResearch:
        def execute(self, _plan):
            return {
                "question": "verify price",
                "tasks": [{
                    "factor_key": "competitive_price",
                    "source_id": "web",
                    "evidence": {
                        "id": "verified-price",
                        "statement": "price verified",
                        "captured_at": "2026-10-07T00:00:00Z",
                        "confidence": 0.95,
                        "observation": {"normalized_value": 110, "unit": "KRW", "currency": "KRW", "raw_value": "110 KRW"},
                    },
                }],
            }

    handlers.research = FakeResearch()
    from core.jobs.queue import InMemoryJobQueue
    from core.jobs.worker import JobWorker
    queue = InMemoryJobQueue()
    queue.enqueue(Job(
        type=JobType.EXECUTE_RESEARCH,
        payload={
            "business_id": "b-loop", "policy_id": "policy-loop-v1", "exposure": 0.8,
            "plan": {"question": "verify price", "tasks": [{
                "factor_key": "competitive_price", "objective": "verify price",
                "method": "web", "priority": 80, "freshness_minutes": 1440,
            }]},
        },
    ))
    worker = JobWorker(queue, handlers=handlers.registry(), retry_base_seconds=0)
    completed = worker.drain(limit=5)

    assert [job.type for job in completed] == [
        JobType.EXECUTE_RESEARCH, JobType.INGEST_RESEARCH,
        JobType.REPROCESS_OBSERVATION, JobType.GENERATE_DECISION,
        JobType.DISPATCH_ACTION,
    ]
    assert completed[-1].result["action"]["kind"] == "alert"
    assert completed[-1].result["alert"]["recommended_action"] == "review"
    assert completed[-1].result["alert"]["impact_score"] == 8.0
    assert len(handlers.store.alerts) == 1


def test_ingest_research_persists_observation_lineage():
    observations = InMemoryObservationRepository()
    handlers = JobHandlers(observation_repository=observations)
    result = handlers.ingest_research(
        Job(
            type=JobType.INGEST_RESEARCH,
            payload={
                "business_id": "b-research",
                "research": {
                    "question": "verify competitor price",
                    "tasks": [{
                        "factor_key": "competitive_price",
                        "source_id": "web-source",
                        "evidence": {
                            "id": "ev-1",
                            "statement": "Observed competitor price",
                            "captured_at": "2026-10-07T00:00:00Z",
                            "confidence": 0.9,
                            "observation": {"normalized_value": 12000, "unit": "KRW", "currency": "KRW", "raw_value": "₩12,000"},
                        },
                    }],
                },
            },
        )
    )
    assert result["observation_count"] == 1
    saved = observations.get(result["observations"][0]["id"])
    assert saved is not None
    assert saved.evidence_id == "ev-1"
    assert saved.entity_id == "b-research"
    assert saved.normalized_value == 12000
    assert saved.unit == "KRW"
    assert saved.currency == "KRW"


def test_research_observation_reprocessing_builds_measurement_signal_and_impact():
    from core.measurement.repository import InMemoryMeasurementRepository

    observations = InMemoryObservationRepository()
    measurements = InMemoryMeasurementRepository()
    signals = InMemorySignalRepository()
    impacts = InMemoryImpactRepository()
    handlers = JobHandlers(
        observation_repository=observations,
        measurement_repository=measurements,
        signal_repository=signals,
        impact_repository=impacts,
    )

    for evidence_id, captured_at, value in [
        ("ev-old", "2026-10-06T00:00:00Z", 100),
        ("ev-new", "2026-10-07T00:00:00Z", 110),
    ]:
        result = handlers.ingest_research(Job(
            type=JobType.INGEST_RESEARCH,
            payload={"business_id": "b-loop", "research": {"question": "price", "tasks": [{
                "factor_key": "competitive_price",
                "evidence": {
                    "id": evidence_id,
                    "captured_at": captured_at,
                    "observation": {"normalized_value": value, "unit": "KRW", "currency": "KRW"},
                },
            }]}},
        ))

    result = handlers.reprocess_observation(Job(
        type=JobType.REPROCESS_OBSERVATION,
        payload={
            "observation": result["observations"][0],
            "business_id": "b-loop",
            "policy_id": "policy-v1",
        },
    ))
    assert result["measurement"]["value"] == 0.1
    assert result["signal"]["delta_pct"] == 10.0
    assert result["impact"]["measurement_ids"] == [result["measurement"]["id"]]
    assert result["policy_id"] == "policy-v1"
