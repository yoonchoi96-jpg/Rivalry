from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import PlatformAdapter


class OpenFoodFactsAdapter(PlatformAdapter):
    """Read public product data from Open Food Facts without provider credentials."""

    BASE_URL = "https://world.openfoodfacts.org/api/v2/search"

    def __init__(self, *, opener=urlopen, timeout: float = 10.0) -> None:
        self._opener = opener
        self._timeout = timeout

    def _search(self, competitor: dict[str, object]) -> list[dict[str, object]]:
        query = str(competitor.get("query") or competitor.get("name") or "").strip()
        if not query:
            raise ValueError("Open Food Facts competitor requires payload.competitor.query or name")
        page_size = min(max(int(competitor.get("page_size", 20)), 1), 100)
        params = urlencode({
            "search_terms": query,
            "page_size": page_size,
            "fields": "code,product_name,brands,categories,quantity,nutriscore_grade,url,last_modified_t",
        })
        request = Request(
            f"{self.BASE_URL}?{params}",
            headers={"User-Agent": "Rivalry/0.2 (+competitive-intelligence; contact-required-by-source)"},
        )
        with self._opener(request, timeout=self._timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        products = payload.get("products", [])
        if not isinstance(products, list):
            return []
        return [item for item in products if isinstance(item, dict)]

    def get_products(self, competitor: dict[str, object]) -> list[dict[str, object]]:
        fetched_at = datetime.now(timezone.utc).isoformat()
        normalized = []
        for product in self._search(competitor):
            code = str(product.get("code") or "").strip()
            if not code:
                continue
            normalized.append({
                "id": code,
                "name": str(product.get("product_name") or "").strip(),
                "brand": str(product.get("brands") or "").strip(),
                "categories": str(product.get("categories") or "").strip(),
                "quantity": str(product.get("quantity") or "").strip(),
                "nutriscore_grade": str(product.get("nutriscore_grade") or "").strip(),
                "source": "openfoodfacts",
                "source_url": str(product.get("url") or f"https://world.openfoodfacts.org/product/{code}"),
                "fetched_at": fetched_at,
                "source_updated_at": product.get("last_modified_t"),
            })
        return normalized

    def discover_competitors(self, business: dict[str, object]) -> list[dict[str, object]]:
        return []

    def get_prices(self, competitor: dict[str, object]) -> list[object]:
        return []

    def get_reviews(self, competitor: dict[str, object]) -> list[object]:
        return []

    def get_promotions(self, competitor: dict[str, object]) -> list[object]:
        return []
