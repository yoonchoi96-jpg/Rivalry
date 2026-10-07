import pytest

from adapters.base import PlatformAdapter
from adapters.registry import AdapterRegistry
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType
from core.intelligence.engine import IntelligenceStore


class FakeAdapter(PlatformAdapter):
    def discover_competitors(self, business): return []
    def get_products(self, competitor): return [{"id": "p1"}, {"id": "p2"}]
    def get_prices(self, competitor): return [110]
    def get_reviews(self, competitor): return ["r1"]
    def get_promotions(self, competitor): return ["promo"]


def test_competitor_collection_uses_universal_adapter():
    registry = AdapterRegistry()
    registry.register("KR", "demo", FakeAdapter())
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "kr", "platform": "DEMO", "competitor": {"id": "c1"}})
    result = JobHandlers(adapters=registry).collect_competitor(job)
    assert result["products"] == [{"id": "p1"}, {"id": "p2"}]
    assert result["changes"]
    assert result["changes"][0]["type"] == "NEW_PRODUCT"


def test_competitor_collection_fails_without_adapter():
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "KR", "platform": "missing", "competitor": {"id": "c1"}})
    try:
        JobHandlers().collect_competitor(job)
    except ValueError as exc:
        assert "No adapter registered" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_collection_detects_price_change_on_second_snapshot():
    class PriceAdapter(FakeAdapter):
        def __init__(self): self.price = 100
        def get_prices(self, competitor): return [self.price]

    adapter = PriceAdapter()
    registry = AdapterRegistry()
    registry.register("KR", "demo", adapter)
    handlers = JobHandlers(adapters=registry)
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "KR", "platform": "demo", "competitor": {"id": "c2"}})
    first = handlers.collect_competitor(job)
    assert any(c["type"] == "NEW_PRODUCT" for c in first["changes"])
    adapter.price = 110
    second = handlers.collect_competitor(job)
    assert any(c["type"] == "PRICE_CHANGED" for c in second["changes"])


def test_process_intelligence_returns_recommendation():
    handlers = JobHandlers()
    job = Job(type=JobType.PROCESS_INTELLIGENCE, payload={
        "change": {"id": "ch1", "competitor_id": "c1", "type": "PRICE_CHANGED", "before": 100, "after": 110, "magnitude": 10, "detected_at": "2026-10-04T00:00:00Z"}
    })
    result = handlers.process_intelligence(job)
    assert result["change_id"] == "ch1"
    assert result["recommendation"]["action"] == "monitor_before_matching_price"


def test_build_alert_returns_actionable_alert():
    handlers = JobHandlers()
    change = {"id": "ch1", "competitor_id": "c1", "type": "PRICE_CHANGED", "magnitude": 10, "impact_score": 72, "detected_at": "2026-10-04T00:00:00Z"}
    intelligence = {"summary": "Material price change", "confidence": 80, "hypotheses": [{"type": "cost"}], "recommendation": {"action": "monitor_before_matching_price"}}
    result = handlers.build_alert(Job(type=JobType.BUILD_ALERT, payload={"change": change, "intelligence": intelligence}))
    assert result["likely_cause"] == "cost"
    assert result["recommended_action"] == "monitor_before_matching_price"


def test_dispatch_action_preserves_recommendation_revision_in_alert_identity():
    from core.decision.models import DecisionRecommendation
    from core.impact.models import BusinessImpact
    from core.impact.repository import InMemoryImpactRepository

    store = IntelligenceStore()
    impacts = InMemoryImpactRepository()
    impact = BusinessImpact(
        id="impact-1",
        business_id="b1",
        entity_id="b1",
        signal_id="signal-1",
        factor_key="competitive_price",
        magnitude=0.8,
        exposure=0.75,
        confidence=0.9,
        rationale="competitive pressure",
    )
    impacts.save(impact)
    handlers = JobHandlers(store=store, impact_repository=impacts)

    recommendation = DecisionRecommendation(
        business_id="b1",
        impact_id="impact-1",
        action="review",
        priority=0.8,
        rationale="review now",
        confidence=0.9,
        signal_id="signal-1",
        factor_key="competitive_price",
        policy_id="policy-v1",
    )
    first = handlers.dispatch_action(Job(
        type=JobType.DISPATCH_ACTION,
        payload={"recommendation": recommendation.model_dump(mode="json")},
    ))
    revised = recommendation.model_copy(update={"rationale": "review after verification"})
    second = handlers.dispatch_action(Job(
        type=JobType.DISPATCH_ACTION,
        payload={"recommendation": revised.model_dump(mode="json")},
    ))

    assert first["alert"]["id"] != second["alert"]["id"]
    assert first["alert"]["recommendation_revision"] != second["alert"]["recommendation_revision"]
    assert len(store.all_alerts()) == 2


def test_dispatch_action_persists_canonical_action_for_alias():
    from core.decision.models import DecisionRecommendation
    from core.impact.models import BusinessImpact
    from core.impact.repository import InMemoryImpactRepository

    store = IntelligenceStore()
    impacts = InMemoryImpactRepository()
    impacts.save(BusinessImpact(
        id="impact-alias",
        business_id="b1",
        entity_id="b1",
        signal_id="signal-alias",
        factor_key="competitive_price",
        magnitude=0.6,
        exposure=0.8,
        confidence=0.9,
        rationale="competitive pressure",
    ))
    handlers = JobHandlers(store=store, impact_repository=impacts)
    recommendation = DecisionRecommendation(
        business_id="b1",
        impact_id="impact-alias",
        action="monitor_before_matching_price",
        priority=0.7,
        rationale="monitor before matching",
        confidence=0.9,
        signal_id="signal-alias",
        factor_key="competitive_price",
        policy_id="policy-v1",
    )

    result = handlers.dispatch_action(Job(
        type=JobType.DISPATCH_ACTION,
        payload={"recommendation": recommendation.model_dump(mode="json")},
    ))

    assert result["action"]["action"] == "monitor"
    assert result["alert"]["recommended_action"] == "monitor"
    assert ":monitor:" in result["alert"]["id"]
    assert ":monitor_before_matching_price:" not in result["alert"]["id"]
    assert result["alert"]["impact_score"] == 24.0


def test_dispatch_action_aliases_share_canonical_alert_identity():
    from core.decision.models import DecisionRecommendation
    from core.impact.models import BusinessImpact
    from core.impact.repository import InMemoryImpactRepository

    store = IntelligenceStore()
    impacts = InMemoryImpactRepository()
    impacts.save(BusinessImpact(
        id="impact-alias-identity", business_id="b1", entity_id="b1",
        signal_id="signal-alias", factor_key="competitive_price",
        magnitude=0.6, exposure=0.8, confidence=0.9, rationale="pressure",
    ))
    handlers = JobHandlers(store=store, impact_repository=impacts)
    base = dict(
        business_id="b1", impact_id="impact-alias-identity", priority=0.7,
        rationale="monitor before matching", confidence=0.9,
        signal_id="signal-alias", factor_key="competitive_price", policy_id="policy-v1",
    )
    canonical = DecisionRecommendation(action="monitor", **base)
    alias = DecisionRecommendation(action="watch", **base)

    first = handlers.dispatch_action(Job(type=JobType.DISPATCH_ACTION, payload={"recommendation": canonical.model_dump(mode="json")}))
    second = handlers.dispatch_action(Job(type=JobType.DISPATCH_ACTION, payload={"recommendation": alias.model_dump(mode="json")}))

    assert first["alert"]["id"] == second["alert"]["id"]
    assert first["alert"]["recommendation_revision"] == second["alert"]["recommendation_revision"]
    assert len(store.all_alerts()) == 1


def test_ingest_research_requires_observation_repository():
    handlers = JobHandlers()
    with pytest.raises(RuntimeError, match="observation repository is not configured"):
        handlers.ingest_research(Job(
            type=JobType.INGEST_RESEARCH,
            payload={"research": {"question": "q", "tasks": []}, "business_id": "b1"},
        ))


def test_ingest_research_assigns_distinct_ids_without_evidence_ids():
    from core.observation.repository import InMemoryObservationRepository

    observations = InMemoryObservationRepository()
    handlers = JobHandlers(observation_repository=observations)
    result = handlers.ingest_research(Job(
        type=JobType.INGEST_RESEARCH,
        payload={
            "business_id": "b1",
            "research": {
                "question": "compare prices",
                "tasks": [
                    {
                        "factor_key": "competitive_price",
                        "source_id": "source-a",
                        "evidence": {"statement": "price is 100", "captured_at": "2026-10-07T00:00:00Z"},
                    },
                    {
                        "factor_key": "competitive_price",
                        "source_id": "source-b",
                        "evidence": {"statement": "price is 120", "captured_at": "2026-10-07T00:01:00Z"},
                    },
                ],
            },
        },
    ))

    assert result["observation_count"] == 2
    assert result["observations"][0]["id"] != result["observations"][1]["id"]
    assert observations.get(result["observations"][0]["id"]) is not None
    assert observations.get(result["observations"][1]["id"]) is not None


def test_analyze_reviews_returns_summary():
    handlers = JobHandlers()
    result = handlers.analyze_reviews(Job(type=JobType.ANALYZE_REVIEWS, payload={
        "reviews": [
            {"id": "r1", "competitor_id": "c1", "rating": 5, "created_at": "2026-10-04T00:00:00Z", "sentiment": "positive", "topics": ["taste"]},
            {"id": "r2", "competitor_id": "c1", "rating": 2, "created_at": "2026-10-04T00:00:00Z", "sentiment": "negative", "topics": ["delivery"]},
        ],
    }))
    assert result["review_count"] == 2
    assert result["positive_count"] == 1
    assert result["negative_count"] == 1


def test_generate_prediction_requires_repeated_signal():
    handlers = JobHandlers()
    result = handlers.generate_prediction(Job(type=JobType.GENERATE_PREDICTION, payload={
        "competitor_id": "c1",
        "changes": [
            {"id": "a", "competitor_id": "c1", "type": "PRICE_CHANGED", "magnitude": 5, "detected_at": "2026-10-04T00:00:00Z"},
            {"id": "b", "competitor_id": "c1", "type": "PRICE_CHANGED", "magnitude": 6, "detected_at": "2026-10-04T00:00:00Z"},
        ],
    }))
    assert result["prediction"]["competitor_id"] == "c1"
    assert result["prediction"]["evidence_change_ids"] == ["a", "b"]


def test_worker_outputs_are_visible_in_intelligence_store():
    store = IntelligenceStore()
    handlers = JobHandlers(store=store)
    change = {"id": "ch-store", "competitor_id": "c1", "type": "PRICE_CHANGED", "magnitude": 10, "impact_score": 72, "detected_at": "2026-10-04T00:00:00Z"}
    alert = handlers.build_alert(Job(type=JobType.BUILD_ALERT, payload={
        "change": change,
        "intelligence": {"summary": "Material price change", "confidence": 80, "hypotheses": [{"type": "cost"}], "recommendation": {"action": "monitor_before_matching_price"}},
    }))
    assert store.alerts_for("c1") == [alert]

    prediction = handlers.generate_prediction(Job(type=JobType.GENERATE_PREDICTION, payload={
        "competitor_id": "c1",
        "changes": [
            {**change, "id": "a"},
            {**change, "id": "b"},
        ],
    }))
    assert store.predictions_for("c1")[0].id == prediction["prediction"]["id"]


def test_collection_snapshot_is_kept_in_intelligence_store():
    class PriceAdapter(FakeAdapter):
        def __init__(self): self.price = 100
        def get_prices(self, competitor): return [self.price]

    adapter = PriceAdapter()
    registry = AdapterRegistry()
    registry.register("KR", "demo", adapter)
    store = IntelligenceStore()
    handlers = JobHandlers(adapters=registry, store=store)
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "KR", "platform": "demo", "competitor": {"id": "c-snapshot"}})

    handlers.collect_competitor(job)
    assert store.latest_snapshot("c-snapshot")["prices"] == [100]

    adapter.price = 110
    result = handlers.collect_competitor(job)
    assert any(change["type"] == "PRICE_CHANGED" for change in result["changes"])


def test_two_stores_share_repository_state():
    from core.intelligence.repository import InMemoryIntelligenceRepository

    repository = InMemoryIntelligenceRepository()
    first = IntelligenceStore(repository=repository)
    second = IntelligenceStore(repository=repository)

    first.record_snapshot("c-shared", {"prices": [100], "products": []})
    assert second.latest_snapshot("c-shared")["prices"] == [100]

    from core.intelligence.models import Change
    change = Change(
        id="shared-change",
        business_id=None,
        competitor_id="c-shared",
        type="PRICE_CHANGED",
        before=100,
        after=110,
        magnitude=10,
        detected_at="2026-10-04T00:00:00Z",
    )
    first.record_changes([change])
    assert [item.id for item in second.competitor_history("c-shared")] == ["shared-change"]

def test_ingest_research_rejects_non_list_tasks():
    from core.observation.repository import InMemoryObservationRepository

    handlers = JobHandlers(observation_repository=InMemoryObservationRepository())
    with pytest.raises(ValueError, match="tasks to be a list"):
        handlers.ingest_research(Job(
            type=JobType.INGEST_RESEARCH,
            payload={"business_id": "b1", "research": {"question": "q", "tasks": {}}},
        ))


def test_ingest_research_rejects_evidence_without_timestamp():
    from core.observation.repository import InMemoryObservationRepository

    handlers = JobHandlers(observation_repository=InMemoryObservationRepository())
    with pytest.raises(ValueError, match="requires observed_at or captured_at"):
        handlers.ingest_research(Job(
            type=JobType.INGEST_RESEARCH,
            payload={
                "business_id": "b1",
                "research": {
                    "question": "q",
                    "tasks": [{
                        "factor_key": "competitive_price",
                        "source_id": "source-a",
                        "evidence": {"statement": "price is 100"},
                    }],
                },
            },
        ))
