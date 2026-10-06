from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.causal.builder import build_causal_map
from core.intent.models import IntentKind
from core.jobs.runtime import business_repository
from core.research.planner import build_research_plan

router = APIRouter(prefix="/research", tags=["research"])


class ResearchPlanRequest(BaseModel):
    business_id: str
    question: str = Field(min_length=1)
    intent: IntentKind = IntentKind.UNDERSTAND


@router.post("/plan")
def research_plan(request: ResearchPlanRequest):
    business = business_repository.get(request.business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="business not found")
    causal_map = build_causal_map(request.question, business, intent=request.intent)
    return {
        "causal_map": causal_map,
        "research_plan": build_research_plan(causal_map),
    }
