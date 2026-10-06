from __future__ import annotations
from enum import StrEnum
from pydantic import BaseModel, Field

class QAStage(StrEnum):
    SOURCE = "source"
    EXTRACTION = "extraction"
    ENTITY = "entity"
    NORMALIZATION = "normalization"
    MEASUREMENT = "measurement"
    SIGNAL = "signal"
    REASONING = "reasoning"
    RECOMMENDATION = "recommendation"

class QAStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

class QAResult(BaseModel):
    stage: QAStage
    status: QAStatus
    score: float = Field(ge=0, le=1)
    checks: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    observation_ids: list[str] = Field(default_factory=list)
    measurement_ids: list[str] = Field(default_factory=list)
