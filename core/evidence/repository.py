from __future__ import annotations

from typing import Protocol

from .models import Evidence, EvidenceSource


class EvidenceRepository(Protocol):
    def save_source(self, source: EvidenceSource) -> EvidenceSource: ...
    def save(self, evidence: Evidence) -> Evidence: ...
    def get(self, evidence_id: str) -> Evidence | None: ...


class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self.sources: dict[str, EvidenceSource] = {}
        self.items: dict[str, Evidence] = {}

    def save_source(self, source: EvidenceSource) -> EvidenceSource:
        self.sources[source.id] = EvidenceSource.model_validate(source.model_dump(mode="json"))
        return EvidenceSource.model_validate(self.sources[source.id].model_dump(mode="json"))

    def save(self, evidence: Evidence) -> Evidence:
        if evidence.source_id not in self.sources:
            raise ValueError("Evidence source must exist before evidence")
        self.items[evidence.id] = Evidence.model_validate(evidence.model_dump(mode="json"))
        return Evidence.model_validate(self.items[evidence.id].model_dump(mode="json"))

    def get(self, evidence_id: str) -> Evidence | None:
        item = self.items.get(evidence_id)
        return None if item is None else Evidence.model_validate(item.model_dump(mode="json"))
