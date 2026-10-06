from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.decision.engine import DecisionEngine
from core.decision.models import DecisionPolicy, DecisionRecommendation
from core.impact.models import BusinessImpact
from core.jobs.models import Job, JobType
from core.jobs.runtime import (
    decision_policy_registry,
    decision_recommendation_repository,
    signal_repository,
)

router = APIRouter(prefix="/decision", tags=["decision"])


class DecisionJobRequest(BaseModel):
    impact_id: str
    policy_id: str
    idempotency_key: str | None = None


@router.post("/jobs", response_model=Job, status_code=202)
def enqueue_decision_job(request: DecisionJobRequest):
    from core.jobs.runtime import job_queue
    return job_queue.enqueue(
        Job(
            type=JobType.GENERATE_DECISION,
            payload={"impact_id": request.impact_id, "policy_id": request.policy_id},
            idempotency_key=request.idempotency_key,
        )
    )


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
        recommendation = DecisionEngine().recommend(impact, signal, policy)
        return decision_recommendation_repository.save(recommendation)
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
        recommendation = DecisionEngine().recommend(impact, signal, policy)
        return decision_recommendation_repository.save(recommendation)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recommendations/{business_id}", response_model=list[DecisionRecommendation])
def list_recommendations(business_id: str):
    return decision_recommendation_repository.list_for_business(business_id)
