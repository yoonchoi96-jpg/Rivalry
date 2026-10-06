from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.causal.builder import build_causal_map
from core.intent.models import IntentKind
from core.jobs.models import Job, JobType
from core.jobs.runtime import business_repository, job_queue, source_repository
from core.research.models import ResearchPlan
from core.research.planner import build_research_plan

router=APIRouter(prefix="/research",tags=["research"])

class ResearchPlanRequest(BaseModel):
    business_id:str
    question:str=Field(min_length=1)
    intent:IntentKind=IntentKind.UNDERSTAND

class ResearchExecuteRequest(BaseModel):
    plan:ResearchPlan
    idempotency_key:str|None=None

@router.post("/plan")
def research_plan(request:ResearchPlanRequest):
    business=business_repository.get(request.business_id)
    if business is None: raise HTTPException(status_code=404,detail="business not found")
    causal_map=build_causal_map(request.question,business,intent=request.intent)
    return {"causal_map":causal_map,"research_plan":build_research_plan(causal_map,sources=source_repository.list())}

@router.post("/execute",response_model=Job,status_code=202)
def research_execute(request:ResearchExecuteRequest)->Job:
    return job_queue.enqueue(Job(type=JobType.EXECUTE_RESEARCH,payload={"plan":request.plan.model_dump(mode="json")},idempotency_key=request.idempotency_key))
