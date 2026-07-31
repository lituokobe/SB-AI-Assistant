"""TypedDict definition of the LangGraph agent state.

Product Intent:
    The state is the single source of truth that flows through every node in
    the graph.  It accumulates across user turns via the MemorySaver
    checkpointer, allowing the scoping loop (which spans multiple HTTP
    requests) to remember intent, round number, and selections.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict


def append_messages(left: list[dict[str, str]], right: list[dict[str, str]]) -> list[dict[str, str]]:
    """Reducer that appends new messages to the existing list.

    Product Intent:
        Enables multi-turn conversations — each API call adds only the latest
        user message, and the reducer merges it with the persisted history.
    """
    return left + right


class AgentState(TypedDict, total=False):
    """LangGraph state shared across all nodes.

    Fields are grouped by lifecycle stage:

    * **Per-turn input** (set by the API layer each invocation):
        ``messages``, ``user_id``, ``profile``, ``context``
    * **Router output**:
        ``intent``, ``phase``
    * **Scoping output**:
        ``scoping_round``, ``scoping_selections``, ``scoping_buttons``,
        ``scoping_fields``, ``skip_scoping``
    * **Search / guardrail output**:
        ``products``, ``filtered_products``
    * **Response / profile output**:
        ``response``
    """

    # Per-turn input (refreshed by the API each invocation)
    messages: Annotated[list[dict[str, str]], append_messages]
    user_id: str
    profile: dict[str, Any]
    context: dict[str, Any] | None

    # Router output
    intent: str | None
    phase: str  # "new", "scoping", "ready"

    # Scoping output
    scoping_round: int
    scoping_selections: dict[str, Any]
    scoping_buttons: list[str] | None
    scoping_fields: list[dict[str, str]] | None
    skip_scoping: bool

    # Search / guardrail output
    products: list[dict[str, Any]] | None
    filtered_products: list[dict[str, Any]] | None

    # Response output
    response: str | None
