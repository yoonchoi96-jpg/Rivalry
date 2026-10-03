from enum import StrEnum
from pydantic import BaseModel, Field

class Plan(StrEnum):
    FREE = "free"
    PRO = "pro"
    EXPERT = "expert"

class PlanEntitlements(BaseModel):
    plan: Plan
    competitor_limit: int | None = None
    intelligence: bool = False
    prediction: bool = False
    consultant: bool = False

PLANS = {
    Plan.FREE: PlanEntitlements(plan=Plan.FREE, competitor_limit=10),
    Plan.PRO: PlanEntitlements(plan=Plan.PRO, competitor_limit=None, intelligence=True, prediction=True),
    Plan.EXPERT: PlanEntitlements(plan=Plan.EXPERT, competitor_limit=None, intelligence=True, prediction=True, consultant=True),
}
