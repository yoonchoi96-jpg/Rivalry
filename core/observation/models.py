from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from core.evidence.models import AccessMethod, KnowledgeKind


class Observation(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    metric: str
    raw_value: object
    normalized_value: float | None = None
    unit: str | None = None
    currency: str | None = None
    geography: str | None = None
    observed_at: datetime
    source_id: str
    evidence_id: str | None = None
    access_method: AccessMethod
    confidence: float = Field(default=0.5, ge=0, le=1)
    knowledge_kind: KnowledgeKind = KnowledgeKind.FACT
    provenance: dict[str, object] = Field(default_factory=dict)
    model_version: str | None = None
