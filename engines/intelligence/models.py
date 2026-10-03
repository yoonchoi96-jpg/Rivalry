from enum import StrEnum
from pydantic import BaseModel, Field

class CauseType(StrEnum):
    COST = "cost"
    COMPETITION = "competition"
    DEMAND = "demand"
    POSITIONING = "positioning"
    PROPERTY = "property"
    LABOR = "labor"
    LOGISTICS = "logistics"
    UNKNOWN = "unknown"

class CauseHypothesis(BaseModel):
    type: CauseType
    probability: float = Field(ge=0, le=100)
    evidence: list[str] = []
    confidence: float = Field(ge=0, le=100)

class IntelligenceReport(BaseModel):
    change_id: str
    summary: str
    hypotheses: list[CauseHypothesis] = []
    recommended_actions: list[str] = []
    confidence: float = Field(ge=0, le=100)
