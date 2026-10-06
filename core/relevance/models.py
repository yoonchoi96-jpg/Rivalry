from __future__ import annotations

from pydantic import BaseModel, Field

class RelevanceProfile(BaseModel):
    business_id: str
    factor_weights: dict[str, float] = Field(default_factory=dict)
    topic_weights: dict[str, float] = Field(default_factory=dict)

class RelevanceScore(BaseModel):
    business_id: str
    item_id: str
    relevance: float = Field(ge=0, le=1)
    impact: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    priority: float = Field(ge=0, le=1)

def rank_relevance(*, relevance: float, impact: float, confidence: float) -> float:
    return round(max(0.0, min(1.0, relevance * impact * confidence)), 10)
