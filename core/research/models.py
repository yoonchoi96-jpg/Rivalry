from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from core.causal.models import CausalFactor


class ResearchMethod(StrEnum):
    INTERNAL_DATA = "internal_data"
    API = "api"
    WEB = "web"
    CONNECTED_SOURCE = "connected_source"
    USER_QUESTION = "user_question"


class ResearchTask(BaseModel):
    factor_key: str
    objective: str
    method: ResearchMethod
    priority: int = Field(ge=0, le=100)
    freshness_minutes: int | None = Field(default=None, ge=0)


class ResearchPlan(BaseModel):
    question: str
    tasks: list[ResearchTask] = Field(default_factory=list)
