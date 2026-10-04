from __future__ import annotations

from typing import Any

from adapters.registry import AdapterRegistry
from engines.change_detection.models import Change
from engines.intelligence.service import IntelligenceService

from .models import Job, JobType


class JobHandlers:
    """Application handlers kept independent from the queue implementation."""

    def __init__(self, intelligence: IntelligenceService | None = None, adapters: AdapterRegistry | None = None) -> None:
        self.intelligence = intelligence or IntelligenceService()
        self.adapters = adapters or AdapterRegistry()

    def collect_competitor(self, job: Job) -> dict[str, object]:
        country = job.payload.get("country_code")
        platform = job.payload.get("platform")
        competitor = job.payload.get("competitor")
        if not all(isinstance(value, str) and value for value in (country, platform)):
            raise ValueError("collect_competitor requires country_code and platform")
        adapter = self.adapters.get(country, platform)
        if adapter is None:
            raise ValueError(f"No adapter registered for {country}/{platform}")
        if not isinstance(competitor, dict):
            raise ValueError("collect_competitor requires payload.competitor")
        data: dict[str, object] = {"competitor": competitor}
        for name, method in (("products", adapter.get_products), ("prices", adapter.get_prices), ("reviews", adapter.get_reviews), ("promotions", adapter.get_promotions)):
            data[name] = method(competitor)
        return data

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
        return {
            JobType.COLLECT_COMPETITOR: self.collect_competitor,
            JobType.PROCESS_INTELLIGENCE: self.process_intelligence,
        }
