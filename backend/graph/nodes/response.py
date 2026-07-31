"""Final response generation node.

Product Intent:
    After the ``guardrail`` node filters products, this node assembles the
    assistant's textual reply — the natural-language recommendation that the
    user sees in the chat.  In production this would be an LLM call; in this
    prototype the response is assembled from deterministic templates in
    ``mocks/llm_responses.py`` so demos are fully reproducible.

    Keeping this step separate from ``guardrail`` follows the separation-of-
    concerns rule: filtering (deterministic validation) is distinct from
    response generation (mocked LLM output).
"""

from __future__ import annotations

from typing import Any


def generate_response(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final assistant response from filtered products.

    Product Intent:
        Takes the guardrail-filtered product list and produces a natural-
        language recommendation message.  The tone of the message is shaped
        by the user's communication-style preference from the profile (e.g.,
        concise, casual, detail-focused).

    Args:
        state: The current LangGraph state, expected to contain filtered
            products, the user profile, and conversation context.

    Returns:
        A state update containing the assistant's response text and any
        structured product data for the frontend to render.
    """
    # TODO: implement template-based response generation (mocked LLM) reading
    # from mocks/llm_responses.py.  Tone should be adapted based on
    # state["profile"]["com_style"].
    raise NotImplementedError
