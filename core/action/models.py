from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ActionKind(StrEnum):
    ALERT = "alert"
    RESEARCH = "research"


class RecommendationAction(BaseModel):
    recommendation_id: str
    business_id: str
    action: str
    kind: ActionKind
    priority: float = Field(ge=0, le=1)
    rationale: str
    confidence: float = Field(ge=0, le=1)
    impact_id: str
    signal_id: str
    factor_key: str
    policy_id: str | None = None
