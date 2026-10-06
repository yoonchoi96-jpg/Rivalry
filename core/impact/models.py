from __future__ import annotations

from pydantic import BaseModel, Field


class BusinessImpact(BaseModel):
    id: str
    business_id: str
    entity_id: str
    signal_id: str
    factor_key: str
    exposure: float = Field(default=0.5, ge=0, le=1)
    magnitude: float
    magnitude_low: float | None = None
    magnitude_high: float | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    significance: float = Field(default=0.5, ge=0, le=1)
    rationale: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    observation_ids: list[str] = Field(default_factory=list)
    measurement_ids: list[str] = Field(default_factory=list)
    signal_id: str
