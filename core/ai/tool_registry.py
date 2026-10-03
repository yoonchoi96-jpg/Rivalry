from __future__ import annotations

from typing import Any, Callable

from .tools import rivalry_tool_definitions

ToolHandler = Callable[[dict[str, Any]], Any]


class RivalryToolRegistry:
    """Maps model-visible tool names to application services.

    Production services can be injected here without changing the AI runtime.
    """

    TOOL_NAMES = tuple(
        item["name"]
        for item in rivalry_tool_definitions()
        if item.get("type") == "function"
    )

    def __init__(self, handlers: dict[str, ToolHandler] | None = None):
        self.handlers = handlers or {}

    def definitions(self) -> list[dict[str, Any]]:
        return rivalry_tool_definitions()

    def handlers_for_runtime(self) -> dict[str, ToolHandler]:
        return {
            name: self.handlers.get(name, self._unavailable(name))
            for name in self.TOOL_NAMES
        }

    @staticmethod
    def _unavailable(name: str) -> ToolHandler:
        def handler(arguments: dict[str, Any]) -> dict[str, Any]:
            return {
                "available": False,
                "tool": name,
                "message": "Rivalry data service is not connected yet; do not infer missing data.",
            }

        return handler
