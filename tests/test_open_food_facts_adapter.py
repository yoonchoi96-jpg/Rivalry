import json

from adapters.open_food_facts import OpenFoodFactsAdapter


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_open_food_facts_normalizes_public_products():
    requests = []

    def opener(request, timeout):
        requests.append((request.full_url, timeout))
        return FakeResponse({
            "products": [{
                "code": "123",
                "product_name": "Example",
                "brands": "Example Brand",
                "categories": "snacks",
                "quantity": "100 g",
                "nutriscore_grade": "b",
                "url": "https://world.openfoodfacts.org/product/123",
                "last_modified_t": 1234567890,
            }]
        })

    products = OpenFoodFactsAdapter(opener=opener).get_products({
        "query": "Example Brand",
        "page_size": 5,
    })

    assert len(products) == 1
    assert products[0]["id"] == "123"
    assert products[0]["name"] == "Example"
    assert products[0]["source"] == "openfoodfacts"
    assert products[0]["source_url"].startswith("https://")
    assert "search_terms=Example+Brand" in requests[0][0]
    assert requests[0][1] == 10.0


def test_open_food_facts_requires_a_search_query():
    adapter = OpenFoodFactsAdapter(opener=lambda *_args, **_kwargs: None)
    try:
        adapter.get_products({})
    except ValueError as exc:
        assert "query" in str(exc)
    else:
        raise AssertionError("expected ValueError")
