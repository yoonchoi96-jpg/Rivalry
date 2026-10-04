from __future__ import annotations

from typing import Any

from engines.change_detection.models import Change
from engines.intelligence.service import IntelligenceService

from .models import Job, JobType


class JobHandlers:
    """Application handlers kept independent from the queue implementation."""

    def __init__(self, intelligence: IntelligenceService | None = None) -> None:
        self.intelligence = intelligence or IntelligenceService()

    def process_intelligence(self, job: Job) -> dict[str, object]:
        raw_change = job.payload.get("change")
        if not isinstance(raw_change, dict):
            raise ValueError("process_intelligence requires payload.change")
        change = Change.model_validate(raw_change)
        report = self.intelligence.analyze_change(
            change,
            market_relevance=float(job.payload.get("market_relevance", 50)),
            competitor_importance=float(job.payload.get("competitor_importance", 50)),
            persistence=float(job.payload.get("persistence", 50)),
            evidence=[str(item) for item in job.payload.get("evidence", []) if isinstance(item, str)],
        )
        return report.model_dump(mode="json")

    def registry(self) -> dict[JobType, Any]:
        return {JobType.PROCESS_INTELLIGENCE: self.process_intelligence}
