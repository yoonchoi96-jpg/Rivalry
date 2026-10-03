from __future__ import annotations

from typing import Any


def rivalry_tool_definitions() -> list[dict[str, Any]]:
    """Tool contracts exposed to the AI; implementations will call Rivalry services."""
    return [
        {
            "type": "function",
            "name": "get_today_changes",
            "description": "Return important competitor changes for a business in a recent time window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "business_id": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "required": ["business_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_competitor_history",
            "description": "Return historical changes and detected behavior patterns for a competitor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "competitor_id": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 3650},
                },
                "required": ["competitor_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_review_trends",
            "description": "Summarize recent review sentiment, ratings, and topics for a competitor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "competitor_id": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 30},
                },
                "required": ["competitor_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_cost_signals",
            "description": "Return external input-cost and market signals relevant to a product or price change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 90},
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]
