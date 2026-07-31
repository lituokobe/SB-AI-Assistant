"""Context window assembly — the "harness engineering" layer.

Product Intent:
    Combines the user profile, session summary, and last 3 conversations into
    a single context dict that is passed into the graph state at the start of
    every interaction.  This is what makes the assistant feel personalised —
    it silently shapes responses without ever saying "I remember you."
"""

from __future__ import annotations

from typing import Any

from backend.memory.history import get_recent_conversations, get_session_summary
from backend.memory.profile import load_profile


def assemble_context(user_id: str) -> dict[str, Any]:
    """Assemble the full context window for a user.

    Product Intent:
        This is the harness — the structured profile, a summary of historical
        chats, and the most recent three conversations are combined into a
        single context object that shapes every future interaction.

    Returns:
        A dict with keys ``profile``, ``summary``, and ``recent_conversations``.
    """
    profile = load_profile(user_id)
    summary = get_session_summary(user_id)
    recent_conversations = get_recent_conversations(user_id)

    return {
        "profile": profile,
        "summary": summary,
        "recent_conversations": recent_conversations,
    }
