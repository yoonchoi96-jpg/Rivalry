from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from engines.change_detection.detector import detect_new_product, detect_price_change
from engines.change_detection.models import Change


def normalize_collection(payload: dict[str, object]) -> dict[str, object]:
    """Convert adapter output into stable, pipeline-friendly collections."""
    return {
        "competitor": payload.get("competitor", {}),
        "products": list(payload.get("products", [])) if isinstance(payload.get("products"), list) else [],
        "prices": list(payload.get("prices", [])) if isinstance(payload.get("prices"), list) else [],
        "reviews": list(payload.get("reviews", [])) if isinstance(payload.get("reviews"), list) else [],
        "promotions": list(payload.get("promotions", [])) if isinstance(payload.get("promotions"), list) else [],
    }


def detect_changes(competitor_id: str, before: dict[str, object], after: dict[str, object], source: str = "", business_id: str | None = None) -> list[Change]:
    changes: list[Change] = []
    old_prices = before.get("prices", [])
    new_prices = after.get("prices", [])
    if isinstance(old_prices, list) and isinstance(new_prices, list):
        for old, new in zip(old_prices, new_prices):
            detected = detect_price_change(old, new)
            if detected:
                changes.append(Change(id=str(uuid4()), competitor_id=competitor_id, detected_at=datetime.now(timezone.utc).isoformat(), source=source, business_id=business_id, **detected))
    old_products = before.get("products", [])
    new_products = after.get("products", [])
    if isinstance(new_products, list) and isinstance(old_products, list):
        old_ids = {str(item.get("id")) for item in old_products if isinstance(item, dict) and item.get("id") is not None}
        for product in new_products:
            if isinstance(product, dict) and product.get("id") is not None and str(product["id"]) not in old_ids:
                detected = detect_new_product(None, product)
                changes.append(Change(id=str(uuid4()), competitor_id=competitor_id, detected_at=datetime.now(timezone.utc).isoformat(), source=source, **detected))
    return changes
