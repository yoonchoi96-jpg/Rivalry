from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MeasurementQuality(StrEnum):
    RAW = "raw"
    ESTIMATED = "estimated"
    INFERRED = "inferred"
    VALIDATED = "validated"


class MeasurementDefinition(BaseModel):
    key: str
    required_entities: list[str] = Field(default_factory=list)
    input_metrics: list[str] = Field(default_factory=list)
    formula: str
    unit: str
    time_window: str
    geography: str | None = None
    freshness_minutes: int | None = Field(default=None, ge=0)
    quality_rules: list[str] = Field(default_factory=list)
    applicable_business_types: list[str] = Field(default_factory=list)


class Measurement(BaseModel):
    id: str
    definition_key: str
    entity_id: str
    value: float
    unit: str
    measured_at: str
    time_window: str
    geography: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    quality: MeasurementQuality = MeasurementQuality.RAW
    formula: str
    model_version: str | None = None
    observation_ids: list[str] = Field(default_factory=list)
