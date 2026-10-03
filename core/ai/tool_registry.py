from __future__ import annotations

from typing import Any, Callable

from .tools import rivalry_tool_definitions

ToolHandler = Callable[[dict[str, Any]], Any]


class RivalryToolRegistry:
    """Maps model-visible tools to application intelligence services."""

    TOOL_NAMES = tuple(
        item["name"]
        for item in rivalry_tool_definitions()
        if item.get("type") == "function"
    )

    def __init__(
        self,
        handlers: dict[str, ToolHandler] | None = None,
        intelligence_store: Any | None = None,
    ):
        self.handlers = handlers or {}
        self.intelligence_store = intelligence_store

    def definitions(self) -> list[dict[str, Any]]:
        return rivalry_tool_definitions()

    def handlers_for_runtime(self) -> dict[str, ToolHandler]:
        return {
            name: self.handlers.get(name, self._service_handler(name))
            for name in self.TOOL_NAMES
        }

    def _service_handler(self, name: str) -> ToolHandler:
        store = self.intelligence_store
        if store is None:
            return self._unavailable(name)
        mapping = {
            "get_today_changes": lambda a: store.today_changes(a["business_id"], a.get("days", 1)),
            "get_competitor_history": lambda a: store.competitor_history(a["competitor_id"], a.get("days", 30)),
            "get_review_trends": lambda a: store.review_trends(a["competitor_id"], a.get("days", 30)),
            "get_cost_signals": lambda a: store.cost_signals(a["product_id"], a.get("days", 30)),
            "get_rival_profile": lambda a: store.rival_profile(a["competitor_id"]),
            "get_market_pulse": lambda a: store.market_pulse(a["business_id"], a.get("days", 7)),
            "get_predictions": lambda a: store.predictions_for(a["competitor_id"]),
        }
        handler = mapping.get(name)
        return handler or self._unavailable(name)

    @staticmethod
    def _unavailable(name: str) -> ToolHandler:
        def handler(arguments: dict[str, Any]) -> dict[str, Any]:
            return {
                "available": False,
                "tool": name,
                "message": "Rivalry data service is not connected; do not infer missing data.",
            }
        return handler
