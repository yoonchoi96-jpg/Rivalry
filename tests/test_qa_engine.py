from datetime import datetime, timezone
from core.evidence.models import AccessMethod, Evidence, EvidenceSource
from core.measurement.models import Measurement
from core.observation.models import Observation
from core.qa.engine import validate_evidence, validate_measurement, validate_observation, validate_source
from core.qa.models import QAStatus

def test_source_qa_warns_on_missing_url():
    result=validate_source(None,0.8,0.8)
    assert result.status == QAStatus.WARN

def test_evidence_qa_tracks_lineage():
    now=datetime.now(timezone.utc)
    result=validate_evidence(Evidence(id="e1",source_id="s1",statement="price rose",captured_at=now))
    assert result.status == QAStatus.PASS and result.evidence_ids == ["e1"]

def test_observation_qa_requires_unit_for_normalized_value():
    result=validate_observation(Observation(id="o1",entity_id="e",entity_type="product",metric="price",raw_value="10",normalized_value=10,observed_at=datetime.now(timezone.utc),source_id="s",access_method=AccessMethod.API))
    assert result.status == QAStatus.WARN

def test_measurement_qa_requires_lineage():
    result=validate_measurement(Measurement(id="m1",definition_key="x",entity_id="b",value=1,unit="ratio",measured_at="2026-10-06T00:00:00Z",time_window="day",formula="x/y"))
    assert result.status == QAStatus.FAIL
