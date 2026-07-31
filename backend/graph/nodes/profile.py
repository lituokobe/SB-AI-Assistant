"""Profile update graph node.

Product Intent:
    Passively captures user preferences (preferred brands, budget range,
    product categories, travel type, communication style) without ever telling
    the user "I have updated your profile."  The update is implicit — derived
    from the user's queries and button clicks — and shapes future interactions
    through the context window.

    This node sits at the end of the product-recommendation flow
    (router → scoping → search → guardrail → response → **profile**) and is
    also the sole node in the communication-style shortcut path
    (router → **profile** → response).
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import AgentState
from backend.memory.profile import save_profile

# Brand detection keywords
_BRAND_MAP: dict[str, str] = {
    "iphone": "Apple",
    "ipad": "Apple",
    "apple": "Apple",
    "samsung": "Samsung",
    "galaxy": "Samsung",
    "pixel": "Google",
    "google": "Google",
}

# Communication style detection
_STYLE_MAP: dict[str, str] = {
    "casual": "casual",
    "casually": "casual",
    "chill": "casual",
    "concise": "concise",
    "brief": "concise",
    "short": "concise",
    "detailed": "detailed",
    "comprehensive": "detailed",
    "thorough": "detailed",
}

# Interest category detection
_INTEREST_MAP: dict[str, str] = {
    "phone": "Smartphones",
    "iphone": "Smartphones",
    "smartphone": "Smartphones",
    "tablet": "Tablets",
    "ipad": "Tablets",
}


def _detect_brand(text: str) -> str | None:
    """Extract a brand preference from the conversation text."""
    text_lower = text.lower()
    for keyword, brand in _BRAND_MAP.items():
        if keyword in text_lower:
            return brand
    return None


def _detect_com_style(text: str) -> str | None:
    """Extract a communication-style preference from the conversation text."""
    text_lower = text.lower()
    for keyword, style in _STYLE_MAP.items():
        if keyword in text_lower:
            return style
    return None


def _detect_interests(text: str) -> list[str]:
    """Extract product-category interests from the conversation text."""
    text_lower = text.lower()
    interests: list[str] = []
    for keyword, interest in _INTEREST_MAP.items():
        if keyword in text_lower and interest not in interests:
            interests.append(interest)
    return interests


def update_profile(state: AgentState) -> dict[str, Any]:
    """Silently update the user profile based on the current interaction.

    Product Intent:
        This is what makes the assistant feel like it "remembers" the user.
        Every interaction — whether a product query, a button click, or a tone
        request — is mined for preference signals that are persisted to the
        profile and surfaced in future context windows.
    """
    profile: dict[str, Any] = dict(state.get("profile", {}))
    user_id = state.get("user_id", "default_user")
    intent = state.get("intent", "general")

    # Gather all conversation text for keyword extraction
    messages = state.get("messages", [])
    all_text = " ".join(m.get("content", "") for m in messages)
    latest_msg = messages[-1].get("content", "") if messages else ""

    # --- Communication style ---
    if intent == "com_style":
        new_style = _detect_com_style(all_text)
        if new_style:
            profile["com_style"] = new_style

    # --- Digital interests and brand ---
    if intent == "digital":
        new_interests = _detect_interests(all_text)
        existing_interests: list[str] = list(profile.get("interests", []))
        for interest in new_interests:
            if interest not in existing_interests:
                existing_interests.append(interest)
        profile["interests"] = existing_interests

        # Detect brand from the conversation
        brand = _detect_brand(all_text)
        if brand and not profile.get("preferred_brand"):
            profile["preferred_brand"] = brand

        # Also check scoping selections for action-based signals
        selections = state.get("scoping_selections", {})
        action = selections.get("action", "")
        if action == "Find Max Cashback" and "Cashback" not in existing_interests:
            profile["interests"] = existing_interests + ["Cashback"]

    # --- Travel type ---
    if intent == "travel":
        selections = state.get("scoping_selections", {})
        travel_type = selections.get("travel_type")
        if travel_type:
            profile["travel_type"] = travel_type

    # Persist the updated profile
    save_profile(user_id, profile)

    return {"profile": profile}


def route_after_profile(state: AgentState) -> str:
    """Conditional edge: go to response (com_style) or END (all others)."""
    if state.get("intent") == "com_style":
        return "response"
    return "__end__"
