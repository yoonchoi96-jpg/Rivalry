from datetime import datetime, timezone

from core.evidence.models import AccessMethod, Evidence, EvidenceSource, KnowledgeKind
from core.evidence.repository import InMemoryEvidenceRepository
from core.measurement.models import Measurement, MeasurementQuality
from core.measurement.registry import DEFAULT_MEASUREMENTS, MeasurementRegistry
from core.observation.models import Observation
from core.observation.repository import InMemoryObservationRepository


def test_evidence_lineage_requires_existing_source():
    repo = InMemoryEvidenceRepository()
    now = datetime.now(timezone.utc)
    source = EvidenceSource(
        id="src-1", name="Official API", source_type="api",
        access_method=AccessMethod.API, retrieved_at=now,
    )
    repo.save_source(source)
    evidence = repo.save(Evidence(
        id="ev-1", source_id="src-1", statement="price changed",
        captured_at=now, knowledge_kind=KnowledgeKind.FACT,
    ))
    assert evidence.source_id == source.id


def test_observation_preserves_provenance_and_knowledge_kind():
    repo = InMemoryObservationRepository()
    observation = Observation(
        id="obs-1", entity_id="p-1", entity_type="product", metric="price",
        raw_value="12000", normalized_value=12000, unit="KRW",
        observed_at=datetime.now(timezone.utc), source_id="src-1",
        access_method=AccessMethod.API, knowledge_kind=KnowledgeKind.ESTIMATE,
        provenance={"parser": "v1"},
    )
    saved = repo.save(observation)
    assert saved.knowledge_kind == KnowledgeKind.ESTIMATE
    assert saved.provenance["parser"] == "v1"


def test_measurement_registry_is_declarative():
    registry = MeasurementRegistry(DEFAULT_MEASUREMENTS)
    definition = registry.get("competitive_price_pressure")
    assert definition is not None
    assert "price" in definition.input_metrics
    assert definition.formula
    measurement = Measurement(
        id="m-1", definition_key=definition.key, entity_id="biz-1",
        value=0.1, unit="ratio", measured_at="2026-10-06T00:00:00Z",
        time_window=definition.time_window, formula=definition.formula,
        quality=MeasurementQuality.ESTIMATED, observation_ids=["obs-1"],
    )
    assert measurement.observation_ids == ["obs-1"]
