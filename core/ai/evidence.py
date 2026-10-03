from __future__ import annotations

from pydantic import BaseModel, Field


class AIProviderEvidence(BaseModel):
    provider: str
    model: str
    available: bool = True
    text: str = ""
    latency_ms: int | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    error: str | None = None


class MultiAIReport(BaseModel):
    final_text: str
    final_model: str
    confidence: float = Field(default=0, ge=0, le=100)
    evidence: list[AIProviderEvidence] = Field(default_factory=list)
