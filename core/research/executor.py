from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.evidence.models import AccessMethod, Evidence, EvidenceSource, KnowledgeKind
from core.evidence.repository import EvidenceRepository
from core.qa.engine import validate_evidence, validate_source
from core.qa.models import QAStatus
from core.research.models import ResearchPlan, ResearchTask
from core.source.models import SourceProfile, SourceRequest
from core.source.repository import SourceRepository
from core.source.router import build_source_route_plan


ResearchHandler = Callable[[ResearchTask, SourceProfile], dict[str, Any]]


class ResearchExecutor:
    """Execute research tasks through registered sources and persist evidence.

    Network access is deliberately injected through handlers so the core stays
    provider-agnostic and testable.
    """

    def __init__(
        self,
        sources: SourceRepository,
        evidence: EvidenceRepository,
        handlers: dict[str, ResearchHandler] | None = None,
    ) -> None:
        self.sources = sources
        self.evidence = evidence
        self.handlers = handlers or {}

    @staticmethod
    def _access_method(kind: str) -> AccessMethod:
        return AccessMethod(kind) if kind in {item.value for item in AccessMethod} else AccessMethod.WEB

    def execute(self, plan: ResearchPlan) -> dict[str, object]:
        results: list[dict[str, object]] = []
        for task in plan.tasks:
            results.append(self._execute_task(task))
        return {"question": plan.question, "tasks": results}

    def _execute_task(self, task: ResearchTask) -> dict[str, object]:
        sources = self.sources.list()
        request = SourceRequest(metric=task.factor_key, freshness_minutes=task.freshness_minutes)
        routes = build_source_route_plan(request, sources).routes
        if task.source_id:
            routes = [route for route in routes if route.source_id == task.source_id] + [
                route for route in routes if route.source_id != task.source_id
            ]
        if not routes:
            raise ValueError(f"No source available for research task: {task.factor_key}")

        errors: list[str] = []
        for route in routes:
            source = self.sources.get(route.source_id)
            if source is None:
                continue
            handler = self.handlers.get(source.id)
            if handler is None:
                errors.append(f"{source.id}: no handler")
                continue
            try:
                payload = handler(task, source)
                statement = str(payload.get("statement") or "").strip()
                if not statement:
                    raise ValueError("source handler returned no statement")
                now = datetime.now(timezone.utc)
                source_record = EvidenceSource(
                    id=source.id,
                    name=source.name,
                    url=str(payload["url"]) if payload.get("url") else None,
                    source_type=source.kind.value,
                    access_method=self._access_method(source.kind.value),
                    retrieved_at=now,
                    reliability=source.reliability,
                    coverage=source.coverage,
                    content_hash=str(payload["content_hash"]) if payload.get("content_hash") else None,
                    metadata={**payload.get("metadata", {}), "research_factor": task.factor_key},
                )
                source_qa = validate_source(source_record.url, source_record.reliability, source_record.coverage)
                if source_qa.status == QAStatus.FAIL:
                    raise ValueError("source QA failed")
                self.evidence.save_source(source_record)
                evidence = Evidence(
                    id=str(uuid4()),
                    source_id=source.id,
                    statement=statement,
                    captured_at=now,
                    locator=str(payload["locator"]) if payload.get("locator") else None,
                    excerpt=str(payload["excerpt"]) if payload.get("excerpt") else None,
                    confidence=float(payload.get("confidence", source.reliability)),
                    knowledge_kind=KnowledgeKind(str(payload.get("knowledge_kind", KnowledgeKind.FACT.value))),
                )
                evidence_qa = validate_evidence(evidence)
                if evidence_qa.status == QAStatus.FAIL:
                    raise ValueError("evidence QA failed")
                saved = self.evidence.save(evidence)
                return {
                    "factor_key": task.factor_key,
                    "source_id": source.id,
                    "method": source.kind.value,
                    "evidence": saved.model_dump(mode="json"),
                    "qa": {"source": source_qa.model_dump(mode="json"), "evidence": evidence_qa.model_dump(mode="json")},
                }
            except Exception as exc:
                errors.append(f"{source.id}: {exc}")
        raise RuntimeError(f"All research sources failed for {task.factor_key}: {'; '.join(errors)}")
