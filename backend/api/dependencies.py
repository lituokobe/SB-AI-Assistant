"""Dependency injection — graph runner and session management.

Product Intent:
    Bridges the FastAPI layer and the LangGraph core.  The API routes call
    ``run_graph()`` which:
    1. Loads the user profile and assembles the context window.
    2. Invokes the graph with the user's message and ``thread_id = session_id``
       so the MemorySaver restores any persisted state from prior turns.
    3. Returns the final state for the route handler to serialise.
"""

from __future__ import annotations

from typing import Any

from backend.graph.builder import graph
from backend.memory.context import assemble_context
from backend.memory.profile import load_profile


def run_graph(message: str, session_id: str, user_id: str) -> dict[str, Any]:
    """Invoke the LangGraph agent for a single user turn.

    Product Intent:
        Each HTTP /chat call maps to exactly one graph invocation.  The
        MemorySaver keyed by session_id ensures multi-turn flows (like the
        two-round travel scoping) work seamlessly across separate requests.

    Args:
        message: The user's latest input (typed text, button label, or
            comma-separated travel fields).
        session_id: Unique session identifier — used as the LangGraph
            ``thread_id`` for state persistence.
        user_id: User identifier for profile / history lookup.

    Returns:
        The final graph state after the turn completes.
    """
    # Assemble the context window (profile + summary + recent conversations)
    context = assemble_context(user_id)
    profile = context["profile"]

    # Invoke the graph — messages reducer appends to any persisted history
    config: dict[str, Any] = {"configurable": {"thread_id": session_id}}
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "profile": profile,
            "context": context,
        },
        config=config,
    )

    return result


def get_user_profile(user_id: str) -> dict[str, Any]:
    """Load the current user profile (for the sidebar endpoint)."""
    return load_profile(user_id)
