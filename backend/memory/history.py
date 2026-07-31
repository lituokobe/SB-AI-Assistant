"""Conversation history storage and session summary generation.

Product Intent:
    Supports the "harness engineering" approach by persisting the most recent
    three conversations per user and generating an auto-conclusion after each
    session.  Together with the user profile, this data forms the context
    window assembled by ``memory/context.py`` for every future interaction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mocks.llm_responses import generate_summary

_CONVERSATIONS_PATH = Path(__file__).resolve().parents[2] / "mocks" / "conversations.json"

_MAX_CONVERSATIONS = 3


def _read_all() -> dict[str, list[dict[str, Any]]]:
    """Read the entire conversations JSON file."""
    if not _CONVERSATIONS_PATH.exists():
        return {}
    with open(_CONVERSATIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, list):
            return {"default_user": data}
        return data


def _write_all(data: dict[str, list[dict[str, Any]]]) -> None:
    """Write the entire conversations JSON file."""
    with open(_CONVERSATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_recent_conversations(user_id: str, limit: int = _MAX_CONVERSATIONS) -> list[dict[str, Any]]:
    """Return the most recent *limit* conversations for a user.

    Product Intent:
        Provides the "last 3 conversations" portion of the context window.
    """
    all_conversations = _read_all()
    user_convs = all_conversations.get(user_id, [])
    return user_convs[-limit:]


def save_conversation(user_id: str, conversation: dict[str, Any]) -> None:
    """Persist a completed conversation, retaining only the last 3.

    Product Intent:
        After a session ends, the transcript is stored so future interactions
        can include it in the context window.  Older conversations are evicted.
    """
    all_conversations = _read_all()
    user_convs = all_conversations.get(user_id, [])
    user_convs.append(conversation)
    # Evict oldest beyond the retention limit
    if len(user_convs) > _MAX_CONVERSATIONS:
        user_convs = user_convs[-_MAX_CONVERSATIONS:]
    all_conversations[user_id] = user_convs
    _write_all(all_conversations)


def get_session_summary(user_id: str) -> str | None:
    """Return the stored session summary (auto-conclusion) for a user.

    Product Intent:
        The summary is derived from the most recent conversation.  It captures
        durable preferences and is included in every future context window.
    """
    recent = get_recent_conversations(user_id, limit=1)
    if not recent:
        return None
    return recent[-1].get("summary")


def generate_session_summary(conversation: dict[str, Any]) -> str:
    """Produce a mocked session conclusion from a completed conversation.

    Product Intent:
        In production this would be an LLM call.  Here, deterministic keyword
        extraction ensures reproducible demos.
    """
    text = conversation.get("user_input", "")
    if not text:
        messages = conversation.get("messages", [])
        text = " ".join(m.get("content", "") for m in messages)
    return generate_summary(text)
