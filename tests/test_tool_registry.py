from core.ai.tool_registry import RivalryToolRegistry
from core.intelligence.engine import IntelligenceStore
from core.intelligence.models import Change


def test_registry_uses_intelligence_store():
    store = IntelligenceStore(changes=[
        Change(
            id="c1",
            competitor_id="comp",
            type="PRICE_CHANGED",
            magnitude=80,
            impact_score=90,
            confidence=95,
            detected_at="2026-10-04",
        )
    ])
    registry = RivalryToolRegistry(intelligence_store=store)
    result = registry.handlers_for_runtime()["get_competitor_history"](
        {"competitor_id": "comp", "days": 30}
    )
    assert result[0]["id"] == "c1"


def test_registry_exposes_all_intelligence_tools():
    registry = RivalryToolRegistry(intelligence_store=IntelligenceStore())
    handlers = registry.handlers_for_runtime()
    for name in registry.TOOL_NAMES:
        assert name in handlers
        assert callable(handlers[name])
