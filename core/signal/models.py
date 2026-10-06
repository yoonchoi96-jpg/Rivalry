from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from core.evidence.models import KnowledgeKind


class SignalKind(StrEnum):
    CHANGE = "change"
    ANOMALY = "anomaly"
    TREND = "trend"
    THRESHOLD = "threshold"


class SignalDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class Signal(BaseModel):
    id: str
    entity_id: str
    definition_key: str
    signal_kind: SignalKind
    direction: SignalDirection
    current_value: float
    reference_value: float | None = None
    delta: float | None = None
    delta_pct: float | None = None
    detected_at: str
    observation_ids: list[str] = Field(default_factory=list)
    measurement_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    significance: float = Field(default=0.5, ge=0, le=1)
    knowledge_kind: KnowledgeKind = KnowledgeKind.ESTIMATE
    rationale: str = ""
    freshness_minutes: int | None = Field(default=None, ge=0)
