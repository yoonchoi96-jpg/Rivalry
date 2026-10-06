from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field


class SourceKind(StrEnum):
    INTERNAL_DATA = "internal_data"
    API = "api"
    WEB = "web"
    CONNECTED_SOURCE = "connected_source"
    USER_QUESTION = "user_question"


class SourceProfile(BaseModel):
    id: str
    name: str
    kind: SourceKind
    reliability: float = Field(default=0.5, ge=0, le=1)
    coverage: float = Field(default=0.5, ge=0, le=1)
    cost: float = Field(default=0.5, ge=0, le=1)
    latency: float = Field(default=0.5, ge=0, le=1)
    freshness_minutes: int | None = Field(default=None, ge=0)
    rate_limit_per_minute: int | None = Field(default=None, ge=0)
    normalization_quality: float = Field(default=0.5, ge=0, le=1)
    capabilities: list[str] = Field(default_factory=list)


class SourceRequest(BaseModel):
    metric: str
    geography: str | None = None
    freshness_minutes: int | None = Field(default=None, ge=0)
    minimum_reliability: float = Field(default=0.0, ge=0, le=1)
    required_capabilities: list[str] = Field(default_factory=list)


class SourceRoute(BaseModel):
    source_id: str
    score: float = Field(ge=0, le=1)
    rationale: list[str] = Field(default_factory=list)


class SourceRoutePlan(BaseModel):
    request: SourceRequest
    routes: list[SourceRoute] = Field(default_factory=list)
