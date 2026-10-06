from pydantic import BaseModel, Field

class DecisionRecommendation(BaseModel):
    business_id: str
    impact_id: str
    action: str
    priority: float = Field(ge=0, le=1)
    rationale: str
    confidence: float = Field(ge=0, le=1)
    signal_id: str
    factor_key: str
