from __future__ import annotations

from pydantic import BaseModel, Field


class BusinessEntity(BaseModel):
    """Canonical business object anchoring Rivalry's intelligence graph."""

    id: str
    name: str
    country_code: str = Field(min_length=2, max_length=2)
    business_type: str
    channel: str
    location: str | None = None
    website_url: str | None = None
    goal: str | None = None
    profile: dict[str, object] = Field(default_factory=dict)
