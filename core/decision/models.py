from __future__ import annotations

from pydantic import BaseModel, Field


class DecisionPolicyRule(BaseModel):
    factor_key: str = "*"
    min_impact: float = Field(default=0.0, ge=0, le=1)
    max_impact: float = Field(default=1.0, ge=0, le=1)
    action: str
    rationale: str


class DecisionPolicy(BaseModel):
    name: str
    default_action: str
    default_rationale: str
    rules: list[DecisionPolicyRule] = Field(default_factory=list)


class DecisionRecommendation(BaseModel):
    business_id: str
    impact_id: str
    action: str
    priority: float = Field(ge=0, le=1)
    rationale: str
    confidence: float = Field(ge=0, le=1)
    signal_id: str
    factor_key: str
