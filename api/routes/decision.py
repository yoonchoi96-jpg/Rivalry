from fastapi import APIRouter, HTTPException

from core.decision.engine import DecisionEngine
from core.decision.models import DecisionPolicy, DecisionRecommendation
from core.impact.models import BusinessImpact
from core.jobs.runtime import decision_policy_registry, signal_repository

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/policies/{policy_id}", response_model=DecisionPolicy, status_code=201)
def register_policy(policy_id: str, policy: DecisionPolicy):
    try:
        return decision_policy_registry.register(policy_id, policy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/policies", response_model=list[DecisionPolicy])
def list_policies():
    return decision_policy_registry.list()


@router.get("/policies/{policy_id}", response_model=DecisionPolicy)
def get_policy(policy_id: str):
    policy = decision_policy_registry.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="decision policy not found")
    return policy


@router.post("/recommend/{policy_id}", response_model=DecisionRecommendation)
def recommend_with_policy(policy_id: str, impact: BusinessImpact):
    policy = decision_policy_registry.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="decision policy not found")

    signal = signal_repository.get(impact.signal_id)
    if signal is None:
        raise HTTPException(status_code=400, detail="signal not found")

    try:
        return DecisionEngine().recommend(impact, signal, policy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recommend", response_model=DecisionRecommendation)
def recommend(impact: BusinessImpact, policy: DecisionPolicy):
    if policy.id is None or not policy.id.strip():
        raise HTTPException(status_code=400, detail="decision policy id is required")
    signal = signal_repository.get(impact.signal_id)
    if signal is None:
        raise HTTPException(status_code=400, detail="signal not found")

    try:
        return DecisionEngine().recommend(impact, signal, policy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
