from typing import Any

def _numeric_value(value: Any) -> float | None:
    if isinstance(value, dict):
        for key in ("value", "price", "amount", "current_value"):
            candidate = value.get(key)
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                return float(candidate)
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def detect_price_change(before: Any, after: Any):
    if before is None or after is None:
        return None
    before_value = _numeric_value(before)
    after_value = _numeric_value(after)
    if before_value is None or after_value is None or before_value == 0:
        return None
    magnitude = abs((after_value - before_value) / before_value) * 100
    if magnitude == 0:
        return None
    return {"type": "PRICE_CHANGED", "before": before, "after": after, "magnitude": round(magnitude, 2)}

def detect_new_product(before: dict | None, after: dict):
    if before is None:
        return {"type": "NEW_PRODUCT", "before": None, "after": after, "magnitude": 100}
    return None
