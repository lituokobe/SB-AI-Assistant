"""Profile update graph node.

Product Intent:
    This is the graph node responsible for *when* and *what* to update in the
    user profile.  It sits at the end of every product-recommendation flow
    (router -> scoping -> search -> guardrail -> response -> **profile**) and
    is also the *sole* node in the communication-style shortcut path
    (router -> **profile** -> END).

    The actual profile persistence logic lives in ``memory/profile.py``; this
    node contains the business logic that decides which profile fields to
    mutate based on the conversation (e.g., clicking "Compare Models" on an
    iPhone query sets ``preferred_brand = "Apple"``).
"""

from __future__ import annotations

from typing import Any


def update_profile(state: dict[str, Any]) -> dict[str, Any]:
    """Silently update the user profile based on the current interaction.

    Product Intent:
        Passively captures user preferences (preferred brands, budget range,
        product categories, travel type, communication style) without ever
        telling the user "I have updated your profile."  The update is
        implicit — derived from the user's queries and button clicks — and
        shapes future interactions through the context window.

    Args:
        state: The current LangGraph state, containing the user's input,
            selected scoping options, and the current profile.

    Returns:
        A state update containing the mutated user profile.
    """
    # TODO: implement keyword/extraction-based profile updates.  Delegate
    # persistence to memory/profile.py.  Examples:
    #   - "Compare Models" + iPhone query -> preferred_brand = "Apple"
    #   - "Business Trip" -> travel_type = "Business"
    #   - "casual tone" -> com_style = "Casual"
    raise NotImplementedError
