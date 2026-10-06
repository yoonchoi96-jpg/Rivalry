from fastapi import APIRouter
from core.evidence.models import EvidenceSource, Evidence
from core.observation.models import Observation
from core.measurement.models import Measurement
from core.qa.engine import validate_source, validate_evidence, validate_observation, validate_measurement
from core.qa.models import QAResult

router=APIRouter(prefix="/qa",tags=["qa"])

@router.post("/source",response_model=QAResult)
def source_qa(source: EvidenceSource): return validate_source(source.url,source.reliability,source.coverage)

@router.post("/evidence",response_model=QAResult)
def evidence_qa(evidence: Evidence): return validate_evidence(evidence)

@router.post("/observation",response_model=QAResult)
def observation_qa(observation: Observation): return validate_observation(observation)

@router.post("/measurement",response_model=QAResult)
def measurement_qa(measurement: Measurement): return validate_measurement(measurement)
