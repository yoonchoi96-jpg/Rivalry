from fastapi import APIRouter, HTTPException

from core.decision.engine import DecisionEngine
from core.decision.models import DecisionPolicy, DecisionRecommendation
from core.impact.models import BusinessImpact
from core.jobs.runtime import signal_repository

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/recommend", response_model=DecisionRecommendation)
def recommend(impact: BusinessImpact, policy: DecisionPolicy):
    signal = signal_repository.get(impact.signal_id)
    if signal is None:
        raise HTTPException(status_code=400, detail="signal not found")

    try:
        return DecisionEngine().recommend(impact, signal, policy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
