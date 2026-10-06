from datetime import datetime, timezone

from core.measurement.engine import MeasurementEngine
from core.measurement.registry import DEFAULT_MEASUREMENTS, MeasurementRegistry
from core.observation.models import AccessMethod, Observation


def observation(id, value):
    return Observation(
        id=id,
        entity_id="product-1",
        entity_type="competitor_product",
        metric="price",
        raw_value=value,
        normalized_value=value,
        unit="currency",
        currency="USD",
        observed_at=datetime.now(timezone.utc),
        source_id="api",
        access_method=AccessMethod.API,
        confidence=.9,
    )


def test_measurement_engine_preserves_lineage_and_emits_change_signal():
    engine = MeasurementEngine(MeasurementRegistry(DEFAULT_MEASUREMENTS))
    measurement, signal = engine.measure_change(
        "competitive_price_pressure",
        observation("current", 110),
        observation("reference", 100),
    )
    assert measurement.value == .1
    assert measurement.observation_ids == ["current", "reference"]
    assert signal.measurement_ids == [measurement.id]
    assert signal.observation_ids == ["current", "reference"]
    assert signal.direction.value == "up"
    assert signal.delta == .1
