from adapters.base import PlatformAdapter
from adapters.registry import AdapterRegistry
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType


class FakeAdapter(PlatformAdapter):
    def discover_competitors(self, business): return []
    def get_products(self, competitor): return ["p1"]
    def get_prices(self, competitor): return [100]
    def get_reviews(self, competitor): return ["r1"]
    def get_promotions(self, competitor): return ["promo"]


def test_competitor_collection_uses_universal_adapter():
    registry = AdapterRegistry()
    registry.register("KR", "demo", FakeAdapter())
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={
        "country_code": "kr", "platform": "DEMO", "competitor": {"id": "c1"}
    })
    result = JobHandlers(adapters=registry).collect_competitor(job)
    assert result == {"competitor": {"id": "c1"}, "products": ["p1"], "prices": [100], "reviews": ["r1"], "promotions": ["promo"]}


def test_competitor_collection_fails_without_adapter():
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "KR", "platform": "missing", "competitor": {"id": "c1"}})
    try:
        JobHandlers().collect_competitor(job)
    except ValueError as exc:
        assert "No adapter registered" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_intelligence_handler_builds_report():
    job = Job(type=JobType.PROCESS_INTELLIGENCE, payload={
        "change": {
            "id": "ch1", "competitor_id": "c1", "type": "PRICE_CHANGED",
            "magnitude": 40, "impact_score": 0, "confidence": 80,
            "detected_at": "2026-10-04T00:00:00+00:00", "source": "test",
        },
        "market_relevance": 80,
        "competitor_importance": 90,
    })
    result = JobHandlers().process_intelligence(job)
    assert result["change_id"] == "ch1"
    assert result["hypotheses"]
    assert result["confidence"] >= 0


def test_intelligence_handler_requires_change():
    job = Job(type=JobType.PROCESS_INTELLIGENCE)
    try:
        JobHandlers().process_intelligence(job)
    except ValueError as exc:
        assert "payload.change" in str(exc)
    else:
        raise AssertionError("expected ValueError")
