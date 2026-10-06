from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from core.observation.models import Observation
from core.qa.engine import validate_measurement, validate_signal
from core.signal.detector import detect_change
from core.signal.models import Signal, SignalKind
from .models import Measurement, MeasurementQuality
from .registry import MeasurementRegistry


class MeasurementEngine:
    """Turn comparable observations into lineage-preserving measurements and signals."""

    def __init__(self, registry: MeasurementRegistry) -> None:
        self.registry = registry

    def measure_change(
        self,
        definition_key: str,
        current: Observation,
        reference: Observation,
    ) -> tuple[Measurement, Signal]:
        definition = self.registry.get(definition_key)
        if definition is None:
            raise ValueError(f"Unknown measurement definition: {definition_key}")
        if current.entity_id != reference.entity_id:
            raise ValueError("current and reference observations must share an entity")
        if current.normalized_value is None or reference.normalized_value is None:
            raise ValueError("both observations require normalized values")
        if current.unit != reference.unit:
            raise ValueError("current and reference observations must share a unit")
        if current.currency != reference.currency:
            raise ValueError("current and reference observations must share a currency")

        value = round(current.normalized_value / reference.normalized_value - 1, 12)
        confidence = min(current.confidence, reference.confidence)
        measurement_id = sha256(
            f"{definition_key}:{current.id}:{reference.id}".encode("utf-8")
        ).hexdigest()[:32]
        measurement = Measurement(
            id=measurement_id,
            definition_key=definition_key,
            entity_id=current.entity_id,
            value=value,
            unit=definition.unit,
            measured_at=current.observed_at.isoformat(),
            time_window=definition.time_window,
            geography=current.geography,
            confidence=confidence,
            quality=MeasurementQuality.VALIDATED,
            formula=definition.formula,
            observation_ids=[current.id, reference.id],
        )
        qa = validate_measurement(measurement)
        if qa.status.value == "fail":
            raise ValueError("measurement QA failed")

        delta, delta_pct, direction = detect_change(value, 0.0)
        signal_id = sha256(
            f"{definition_key}:change:{measurement_id}".encode("utf-8")
        ).hexdigest()[:32]
        signal = Signal(
            id=signal_id,
            entity_id=current.entity_id,
            definition_key=definition_key,
            signal_kind=SignalKind.CHANGE,
            direction=direction,
            current_value=value,
            reference_value=0.0,
            delta=delta,
            delta_pct=delta_pct,
            detected_at=datetime.now(timezone.utc).isoformat(),
            observation_ids=[current.id, reference.id],
            measurement_ids=[measurement.id],
            confidence=confidence,
            significance=min(1.0, abs(value)),
            rationale=f"{definition_key} changed by {value:.4f} versus reference",
        )
        signal_qa = validate_signal(signal)
        if signal_qa.status.value == "fail":
            raise ValueError("signal QA failed")
        return measurement, signal
