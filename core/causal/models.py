from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class CausalRelation(StrEnum):
    DIRECT = "direct"
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"


class CausalFactor(BaseModel):
    key: str
    label: str
    relation: CausalRelation
    rationale: str
    priority: int = Field(default=50, ge=0, le=100)
    measurable: bool = True


class CausalMap(BaseModel):
    question: str
    factors: list[CausalFactor] = Field(default_factory=list)
