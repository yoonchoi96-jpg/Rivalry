from core.jobs.pipeline import detect_changes, normalize_collection


def test_normalize_collection_keeps_stable_shape():
    result = normalize_collection({"competitor": {"id": "c1"}, "products": [1], "prices": [100]})
    assert result == {"competitor": {"id": "c1"}, "products": [1], "prices": [100], "reviews": [], "promotions": []}


def test_detect_changes_finds_price_and_new_product():
    changes = detect_changes("c1", {"prices": [100], "products": [{"id": "p1"}]}, {"prices": [110], "products": [{"id": "p1"}, {"id": "p2"}]})
    assert {item.type for item in changes} == {"PRICE_CHANGED", "NEW_PRODUCT"}
    assert any(item.magnitude == 10 for item in changes)
