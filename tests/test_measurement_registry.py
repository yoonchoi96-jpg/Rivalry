from core.measurement.registry import DEFAULT_MEASUREMENTS, MeasurementRegistry

def test_default_measurements_have_stable_keys_and_formulas():
    registry=MeasurementRegistry(DEFAULT_MEASUREMENTS)
    keys=[item.key for item in registry.all()]
    assert keys == ["competitive_price_pressure","fx_exposure"]
    assert all(item.formula for item in registry.all())
