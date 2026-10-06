from datetime import datetime, timezone

from core.evidence.repository import InMemoryEvidenceRepository
from core.research.executor import ResearchExecutor
from core.research.models import ResearchMethod, ResearchPlan, ResearchTask
from core.source.models import SourceKind, SourceProfile
from core.source.repository import InMemorySourceRepository


def test_research_executor_persists_evidence_and_qa():
    sources = InMemorySourceRepository()
    sources.save(SourceProfile(
        id="api", name="Official API", kind=SourceKind.API,
        reliability=.95, coverage=.9, normalization_quality=.95, freshness_minutes=10,
    ))
    evidence = InMemoryEvidenceRepository()

    def handler(task, source):
        return {"statement": "price increased 5%", "url": "https://example.com",
                "confidence": .9, "metadata": {"task": task.factor_key}}

    executor = ResearchExecutor(sources, evidence, {"api": handler})
    result = executor.execute(ResearchPlan(question="why?", tasks=[
        ResearchTask(factor_key="competitive_price", objective="verify", method=ResearchMethod.API, priority=90)
    ]))

    item = result["tasks"][0]
    assert item["source_id"] == "api"
    assert item["evidence"]["statement"] == "price increased 5%"
    assert evidence.get(item["evidence"]["id"]) is not None


def test_research_executor_falls_back_when_primary_handler_fails():
    sources = InMemorySourceRepository()
    sources.save(SourceProfile(id="bad", name="Primary", kind=SourceKind.API, reliability=.95, coverage=.9, normalization_quality=.9))
    sources.save(SourceProfile(id="web", name="Fallback", kind=SourceKind.WEB, reliability=.7, coverage=.8, normalization_quality=.8))
    evidence = InMemoryEvidenceRepository()

    def bad(task, source):
        raise TimeoutError("timeout")

    def good(task, source):
        return {"statement": "fallback evidence"}

    executor = ResearchExecutor(sources, evidence, {"bad": bad, "web": good})
    result = executor.execute(ResearchPlan(question="q", tasks=[
        ResearchTask(factor_key="demand", objective="verify", method=ResearchMethod.WEB, priority=80)
    ]))
    assert result["tasks"][0]["source_id"] == "web"
