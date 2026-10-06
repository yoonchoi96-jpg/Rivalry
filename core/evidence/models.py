from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class KnowledgeKind(StrEnum):
    FACT = "fact"
    ESTIMATE = "estimate"
    HYPOTHESIS = "hypothesis"
    PREDICTION = "prediction"


class AccessMethod(StrEnum):
    API = "api"
    WEB = "web"
    CONNECTED_SOURCE = "connected_source"
    INTERNAL = "internal"
    USER = "user"


class EvidenceSource(BaseModel):
    id: str
    name: str
    url: str | None = None
    source_type: str
    access_method: AccessMethod
    retrieved_at: datetime
    reliability: float = Field(default=0.5, ge=0, le=1)
    coverage: float = Field(default=0.5, ge=0, le=1)
    content_hash: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str
    source_id: str
    statement: str
    captured_at: datetime
    locator: str | None = None
    excerpt: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    knowledge_kind: KnowledgeKind = KnowledgeKind.FACT
