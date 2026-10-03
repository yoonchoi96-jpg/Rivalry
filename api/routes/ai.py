from fastapi import APIRouter, HTTPException

from core.ai.gateway import OpenAIGateway
from core.ai.models import AIRequest, AIResponse
from core.ai.tools import rivalry_tool_definitions

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIResponse)
def chat(request: AIRequest):
    try:
        return OpenAIGateway().respond(request, tools=rivalry_tool_definitions())
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI provider request failed") from exc
