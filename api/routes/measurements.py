from __future__ import annotations
from fastapi import APIRouter, HTTPException
from core.evidence.models import Evidence, EvidenceSource
from core.observation.models import Observation
from core.measurement.models import Measurement
from core.measurement.registry import DEFAULT_MEASUREMENTS, MeasurementRegistry
from core.jobs.runtime import evidence_repository, observation_repository, measurement_repository

router=APIRouter(prefix="/measurements",tags=["measurements"])
registry=MeasurementRegistry(DEFAULT_MEASUREMENTS)

@router.post("/sources",response_model=EvidenceSource,status_code=201)
def create_source(source: EvidenceSource):
    return evidence_repository.save_source(source)

@router.post("/evidence",response_model=Evidence,status_code=201)
def create_evidence(evidence: Evidence):
    try: return evidence_repository.save(evidence)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.post("/observations",response_model=Observation,status_code=201)
def create_observation(observation: Observation):
    if observation.evidence_id and evidence_repository.get(observation.evidence_id) is None:
        raise HTTPException(status_code=400,detail="evidence not found")
    return observation_repository.save(observation)

@router.post("",response_model=Measurement,status_code=201)
def create_measurement(measurement: Measurement):
    definition=registry.get(measurement.definition_key)
    if definition is None: raise HTTPException(status_code=400,detail="unknown measurement definition")
    if measurement.formula != definition.formula:
        raise HTTPException(status_code=400,detail="measurement formula does not match registry")
    return measurement_repository.save(measurement)
