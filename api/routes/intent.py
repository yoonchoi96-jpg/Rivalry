from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.business.models import BusinessProfile
from core.intent.engine import build_intent_plan
from core.jobs.runtime import business_repository

router = APIRouter(prefix="/intent", tags=["intent"])

class IntentPlanRequest(BaseModel):
    business_id: str
    text: str = Field(min_length=1)
    known: list[str] = Field(default_factory=list)

@router.post("/plan")
def intent_plan(request: IntentPlanRequest):
    business = business_repository.get(request.business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="business not found")
    profile_data = dict(business.profile)
    if business.goal and not profile_data.get("current_goal"):
        profile_data["current_goal"] = business.goal
    profile = BusinessProfile.model_validate(profile_data)
    known = list(request.known)
    if "business identity" not in known:
        known.append("business identity")
    if business.goal and "current goal" not in known:
        known.append("current goal")
    return build_intent_plan(request.text, profile, known=known)
