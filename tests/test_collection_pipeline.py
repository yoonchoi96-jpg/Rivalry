from core.intelligence.engine import IntelligenceStore
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType


class FakeAdapter:
    def get_products(self, competitor):
        return [{
            "id": "p1",
            "name": "Example",
            "source": "fake",
            "source_url": "https://example.test/p1",
        }]

    def get_prices(self, competitor):
        return []

    def get_reviews(self, competitor):
        return []

    def get_promotions(self, competitor):
        return []

    def discover_competitors(self, business):
        return []


def test_collection_normalizes_snapshots_and_records_changes():
    store = IntelligenceStore()
    handlers = JobHandlers(store=store)
    handlers.adapters.register("KR", "fake", FakeAdapter())

    job = Job(
        type=JobType.COLLECT_COMPETITOR,
        payload={
            "country_code": "KR",
            "platform": "fake",
            "competitor": {
                "id": "c1",
                "business_id": "b1",
                "name": "Example",
            },
        },
    )

    result = handlers.collect_competitor(job)

    assert result["products"][0]["id"] == "p1"
    assert store.latest_snapshot("c1")["products"][0]["source_url"] == "https://example.test/p1"
    assert len(store.changes) == 1
    assert store.changes[0].type == "NEW_PRODUCT"
    assert store.changes[0].business_id == "b1"


def test_default_handlers_register_global_open_food_facts_adapter():
    handlers = JobHandlers(store=IntelligenceStore())
    assert handlers.adapters.get("KR", "openfoodfacts") is not None
