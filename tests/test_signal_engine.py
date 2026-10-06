from core.signal.detector import detect_anomaly, detect_change, detect_threshold, detect_trend
from core.signal.models import SignalDirection, SignalKind, Signal


def test_change_detection_is_directional_and_numeric():
    delta, pct, direction = detect_change(110, 100)
    assert delta == 10
    assert pct == 10
    assert direction == SignalDirection.UP


def test_change_from_zero_keeps_percentage_unknown():
    delta, pct, direction = detect_change(5, 0)
    assert delta == 5
    assert pct is None
    assert direction == SignalDirection.UP


def test_threshold_and_trend():
    assert detect_threshold(120, 100) == SignalDirection.UP
    assert detect_trend([1, 2, 3, 4]) == SignalDirection.UP
    assert detect_trend([4, 3, 2]) == SignalDirection.DOWN


def test_anomaly_requires_sufficient_baseline():
    assert not detect_anomaly(10, [10])
    assert detect_anomaly(20, [10, 10, 10, 10])


def test_signal_keeps_measurement_lineage():
    signal = Signal(
        id="sig-1", entity_id="biz-1", definition_key="competitive_price_pressure",
        signal_kind=SignalKind.CHANGE, direction=SignalDirection.UP,
        current_value=1.1, reference_value=1.0, delta=.1, delta_pct=10,
        detected_at="2026-10-06T00:00:00Z", measurement_ids=["m-1"],
        observation_ids=["obs-1"], confidence=.9, significance=.8,
    )
    assert signal.measurement_ids == ["m-1"]
