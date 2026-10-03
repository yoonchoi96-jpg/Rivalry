from fastapi import APIRouter, HTTPException

from core.ai.models import AIRequest, AIResponse
from core.ai.runtime import AIRuntime
from core.ai.tool_registry import RivalryToolRegistry
from core.ai.orchestrator import MultiAIOrchestrator
from core.intelligence.engine import IntelligenceStore

_intelligence_store = IntelligenceStore()

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/research", response_model=AIResponse)
def research(request: AIRequest):
    try:
        return MultiAIOrchestrator().run(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Multi-AI provider request failed") from exc


@router.post("/chat", response_model=AIResponse)
def chat(request: AIRequest):
    try:
        registry = RivalryToolRegistry(intelligence_store=_intelligence_store)
        runtime = AIRuntime(handlers=registry.handlers_for_runtime())
        return runtime.run(request, tools=registry.definitions())
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI provider request failed") from exc
