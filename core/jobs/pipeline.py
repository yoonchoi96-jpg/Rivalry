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


def _price_key(item: object) -> str | None:
    """Return a stable price identity when the source supplies one."""
    if not isinstance(item, dict):
        return None
    for field in ("product_id", "productId", "sku", "id"):
        value = item.get(field)
        if value is not None and str(value):
            return str(value)
    return None


def _match_prices(before: list[object], after: list[object]) -> list[tuple[object, object]]:
    """Match prices by stable identity; never assume source ordering is stable."""
    old_by_key = {_price_key(item): item for item in before if _price_key(item) is not None}
    new_by_key = {_price_key(item): item for item in after if _price_key(item) is not None}
    matches = [(old_by_key[key], new_by_key[key]) for key in old_by_key.keys() & new_by_key.keys()]
    if matches:
        return matches
    # Legacy adapters may return scalar/identity-free price arrays. Preserve compatibility
    # only when both sides contain no identities and have the same length.
    if len(before) == len(after) and all(_price_key(item) is None for item in before + after):
        return list(zip(before, after))
    return []


def detect_changes(competitor_id: str, before: dict[str, object], after: dict[str, object], source: str = "", business_id: str | None = None) -> list[Change]:
    changes: list[Change] = []
    old_prices = before.get("prices", [])
    new_prices = after.get("prices", [])
    if isinstance(old_prices, list) and isinstance(new_prices, list):
        for old, new in _match_prices(old_prices, new_prices):
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
                changes.append(Change(id=str(uuid4()), competitor_id=competitor_id, detected_at=datetime.now(timezone.utc).isoformat(), source=source, business_id=business_id, **detected))
    return changes
