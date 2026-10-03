from __future__ import annotations

import json
from typing import Any, Callable

from .gateway import OpenAIGateway
from .models import AIRequest, AIResponse

ToolHandler = Callable[[dict[str, Any]], Any]


class AIRuntime:
    """Runs the Responses API tool loop and keeps provider orchestration in one place."""

    def __init__(
        self,
        gateway: OpenAIGateway | None = None,
        handlers: dict[str, ToolHandler] | None = None,
        max_tool_rounds: int = 6,
    ):
        self.gateway = gateway or OpenAIGateway()
        self.handlers = handlers or {}
        self.max_tool_rounds = max_tool_rounds

    def run(
        self,
        request: AIRequest,
        *,
        tools: list[dict[str, Any]] | None = None,
    ) -> AIResponse:
        model = self.gateway.model_for(request.use_case)
        response = self.gateway.client.responses.create(
            model=model,
            instructions=self.gateway._instructions(request.use_case),
            input=request.message,
            tools=tools or None,
        )

        for _ in range(self.max_tool_rounds):
            calls = [
                item for item in getattr(response, "output", [])
                if getattr(item, "type", None) == "function_call"
            ]
            if not calls:
                return self.gateway._response_from(response, model)

            outputs = []
            for call in calls:
                name = getattr(call, "name", "")
                raw_arguments = getattr(call, "arguments", "{}")
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                handler = self.handlers.get(name)
                if handler is None:
                    result: Any = {"error": f"Unknown Rivalry tool: {name}"}
                else:
                    try:
                        result = handler(arguments)
                    except Exception as exc:
                        result = {"error": f"Tool execution failed: {exc.__class__.__name__}"}
                outputs.append({
                    "type": "function_call_output",
                    "call_id": getattr(call, "call_id"),
                    "output": json.dumps(result, ensure_ascii=False, default=str),
                })

            response = self.gateway.client.responses.create(
                model=model,
                instructions=self.gateway._instructions(request.use_case),
                previous_response_id=getattr(response, "id", None),
                input=outputs,
                tools=tools or None,
            )

        raise RuntimeError("AI tool loop exceeded max_tool_rounds")
