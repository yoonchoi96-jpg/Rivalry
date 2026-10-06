from __future__ import annotations

from .models import SignalDirection


def direction(current: float, reference: float, *, epsilon: float = 1e-12) -> SignalDirection:
    delta = current - reference
    if abs(delta) <= epsilon:
        return SignalDirection.NEUTRAL
    return SignalDirection.UP if delta > 0 else SignalDirection.DOWN


def detect_change(current: float, reference: float) -> tuple[float, float, SignalDirection]:
    delta = current - reference
    delta_pct = None if reference == 0 else (delta / abs(reference)) * 100
    return delta, delta_pct, direction(current, reference)


def detect_threshold(current: float, threshold: float) -> SignalDirection | None:
    if current > threshold:
        return SignalDirection.UP
    if current < threshold:
        return SignalDirection.DOWN
    return None


def detect_trend(values: list[float], *, minimum_points: int = 3) -> SignalDirection | None:
    if len(values) < minimum_points:
        return None
    diffs = [b - a for a, b in zip(values, values[1:])]
    if all(d > 0 for d in diffs):
        return SignalDirection.UP
    if all(d < 0 for d in diffs):
        return SignalDirection.DOWN
    return None


def detect_anomaly(current: float, baseline: list[float], *, z_threshold: float = 3.0) -> bool:
    if len(baseline) < 2:
        return False
    mean = sum(baseline) / len(baseline)
    variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
    std = variance ** 0.5
    if std == 0:
        return current != mean
    return abs(current - mean) / std >= z_threshold
