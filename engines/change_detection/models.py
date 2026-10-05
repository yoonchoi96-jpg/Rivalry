from typing import Any

from pydantic import BaseModel, Field


class Change(BaseModel):
    id: str
    business_id: str | None = None
    competitor_id: str
    type: str
    before: Any = None
    after: Any = None
    magnitude: float = 0
    severity: str = "info"
    impact_score: float = Field(0, ge=0, le=100)
    confidence: float = Field(0, ge=0, le=100)
    detected_at: str
    source: str = ""
