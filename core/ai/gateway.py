from __future__ import annotations

import os
from typing import Any

from .models import AIRequest, AIResponse, AIUseCase


DEFAULT_MODELS = {
    AIUseCase.CHAT: os.getenv("RIVALRY_AI_CHAT_MODEL", "gpt-5.6-luna"),
    AIUseCase.INTELLIGENCE: os.getenv("RIVALRY_AI_INTELLIGENCE_MODEL", "gpt-5.6-sol"),
    AIUseCase.EXPERT: os.getenv("RIVALRY_AI_EXPERT_MODEL", "gpt-5.6-sol"),
}


class OpenAIGateway:
    """Thin provider boundary for Rivalry's conversational AI.

    The application talks to this gateway rather than importing an OpenAI
    client throughout the codebase. This keeps provider/model changes local.
    """

    def __init__(self, client: Any | None = None, models: dict[AIUseCase, str] | None = None):
        self._client = client
        self.models = {**DEFAULT_MODELS, **(models or {})}

    @property
    def client(self) -> Any:
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    def model_for(self, use_case: AIUseCase) -> str:
        return self.models[use_case]

    def respond(self, request: AIRequest, *, tools: list[dict[str, Any]] | None = None) -> AIResponse:
        model = self.model_for(request.use_case)
        response = self.client.responses.create(
            model=model,
            instructions=self._instructions(request.use_case),
            input=request.message,
            tools=tools or None,
        )
        return self._response_from(response, model)

    @staticmethod
    def _response_from(response: Any, model: str) -> AIResponse:
        usage = {}
        if getattr(response, "usage", None):
            usage = {
                key: int(value)
                for key, value in {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }.items()
                if value is not None
            }
        return AIResponse(
            text=getattr(response, "output_text", ""),
            model=model,
            response_id=getattr(response, "id", None),
            usage=usage,
        )

    @staticmethod
    def _instructions(use_case: AIUseCase) -> str:
        base = (
            "You are Rivalry, an AI competitive-intelligence assistant. "
            "Answer from verified Rivalry evidence when available. "
            "Never invent competitor costs, margins, events, or platform data. "
            "Clearly distinguish observed facts, estimates, hypotheses, and recommendations."
        )
        if use_case == AIUseCase.EXPERT:
            return base + (
                " Act as a strategic business consultant. Prioritize actions by "
                "expected business impact, evidence strength, and reversibility."
            )
        if use_case == AIUseCase.INTELLIGENCE:
            return base + (
                " Focus on what changed, why it may matter, likely causes, "
                "confidence, and the next action."
            )
        return base
