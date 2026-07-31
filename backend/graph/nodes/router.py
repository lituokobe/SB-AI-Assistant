"""Intent classification node — the entry point of the graph.

Product Intent:
    Determines which vertical (digital, travel, com_style, or general) the
    user's query belongs to.  This is a mocked LLM call: deterministic keyword
    matching replaces a real model so demos are reproducible.

    When the user is mid-scoping (intent already set, phase == "scoping"), the
    router passes through without re-classifying, allowing the scoping node to
    process the button click or field input.
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import AgentState

# Keyword → intent mapping (deterministic, no LLM)
_DIGITAL_KEYWORDS = {"phone", "camera", "tablet", "laptop", "phone", "iphone", "samsung", "pixel", "ipad"}
_TRAVEL_KEYWORDS = {"trip", "flight", "travel", "hotel", "vacation", "sydney", "tokyo", "paris", "london", "book"}
_COM_STYLE_KEYWORDS = {"tone", "talk to me", "casual", "concise", "detailed", "formal", "casually", "chatty"}

# Known destinations for travel extraction
_KNOWN_DESTINATIONS = ["sydney", "tokyo", "paris", "london", "new york"]


def _classify_intent(message: str) -> str:
    """Return one of 'digital', 'travel', 'com_style', or 'general'."""
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in _COM_STYLE_KEYWORDS):
        return "com_style"
    if any(kw in msg_lower for kw in _TRAVEL_KEYWORDS):
        return "travel"
    if any(kw in msg_lower for kw in _DIGITAL_KEYWORDS):
        return "digital"
    return "general"


def _extract_destination(message: str) -> str | None:
    """Extract a known destination from a travel query."""
    msg_lower = message.lower()
    for city in _KNOWN_DESTINATIONS:
        if city in msg_lower:
            return city.title()
    return None


def router_node(state: AgentState) -> dict[str, Any]:
    """Classify the user's intent or pass through during multi-turn scoping.

    Product Intent:
        On the first turn of a new query, this node classifies intent and
        resets all scoping state.  On subsequent turns (button clicks / field
        inputs during scoping), it passes through so the scoping node can
        process the user's selection.
    """
    # Pass through if we're in the middle of a scoping flow
    if state.get("intent") is not None and state.get("phase") == "scoping":
        return {}

    # --- New query: classify intent ---
    message = state["messages"][-1]["content"]
    intent = _classify_intent(message)

    # Reset scoping state for a fresh query
    new_state: dict[str, Any] = {
        "intent": intent,
        "phase": "new",
        "scoping_round": 0,
        "scoping_selections": {},
        "scoping_buttons": None,
        "scoping_fields": None,
        "skip_scoping": False,
        "products": None,
        "filtered_products": None,
        "response": None,
    }

    # Pre-extract destination for travel queries
    if intent == "travel":
        destination = _extract_destination(message)
        if destination:
            new_state["scoping_selections"]["destination"] = destination

    return new_state


def route_after_router(state: AgentState) -> str:
    """Conditional edge: decide which node runs after the router."""
    intent = state.get("intent", "general")
    if intent == "com_style":
        return "profile"
    if intent == "general":
        return "response"
    return "scoping"
