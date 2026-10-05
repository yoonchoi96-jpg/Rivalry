from core.intelligence.engine import IntelligenceStore
from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType
from core.jobs.pipeline import detect_changes


class FakeAdapter:
    def get_products(self, competitor):
        return [{"id": "p1", "name": "Example", "source": "fake", "source_url": "https://example.test/p1"}]

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
    job = Job(type=JobType.COLLECT_COMPETITOR, payload={"country_code": "KR", "platform": "fake", "competitor": {"id": "c1", "business_id": "b1", "name": "Example"}})
    result = handlers.collect_competitor(job)
    assert result["products"][0]["id"] == "p1"
    assert store.latest_snapshot("c1")["products"][0]["source_url"] == "https://example.test/p1"
    assert len(store.changes) == 1
    assert store.changes[0].type == "NEW_PRODUCT"
    assert store.changes[0].business_id == "b1"


def test_default_handlers_register_global_open_food_facts_adapter():
    handlers = JobHandlers(store=IntelligenceStore())
    assert handlers.adapters.get("KR", "openfoodfacts") is not None


def test_price_changes_match_by_product_identity_not_source_order():
    before = {"prices": [{"product_id": "a", "value": 100}, {"product_id": "b", "value": 200}], "products": []}
    after = {"prices": [{"product_id": "b", "value": 200}, {"product_id": "a", "value": 90}], "products": []}
    changes = detect_changes("c1", before, after, source="fake", business_id="b1")
    assert len(changes) == 1
    assert changes[0].before == {"product_id": "a", "value": 100}
    assert changes[0].after == {"product_id": "a", "value": 90}
    assert changes[0].business_id == "b1"


def test_new_product_change_propagates_business_id():
    changes = detect_changes("c1", {"products": []}, {"products": [{"id": "p2", "name": "New"}]}, business_id="b9")
    assert len(changes) == 1
    assert changes[0].type == "NEW_PRODUCT"
    assert changes[0].business_id == "b9"


def test_identity_free_prices_do_not_pair_different_lengths():
    changes = detect_changes("c1", {"prices": [100, 200]}, {"prices": [90]}, source="fake")
    assert changes == []
