from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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
    source_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResearchPlan(BaseModel):
    question: str
    tasks: list[ResearchTask] = Field(default_factory=list)
