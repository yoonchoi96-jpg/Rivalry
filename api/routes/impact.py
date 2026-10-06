from fastapi import APIRouter, HTTPException

from core.impact.models import BusinessImpact
from core.impact.scorer import score_impact
from core.jobs.runtime import impact_repository, signal_repository
from core.qa.engine import validate_signal

router=APIRouter(prefix="/impact",tags=["impact"])

@router.post("",response_model=BusinessImpact,status_code=201)
def create_impact(impact: BusinessImpact):
    signal=signal_repository.get(impact.signal_id)
    if signal is None:
        raise HTTPException(status_code=400,detail="signal not found")
    qa=validate_signal(signal)
    if qa.status.value == "fail":
        raise HTTPException(status_code=400,detail=qa.issues)
    if impact.entity_id != signal.entity_id:
        raise HTTPException(status_code=400,detail="impact entity does not match signal")
    if impact.observation_ids != signal.observation_ids or impact.measurement_ids != signal.measurement_ids:
        raise HTTPException(status_code=400,detail="impact lineage must match signal lineage")
    return impact_repository.save(impact)

@router.post("/score")
def impact_score(impact: BusinessImpact):
    return {"impact_score": score_impact(impact)}
