"""User profile CRUD — load and persist profiles to ``mocks/user_profiles.json``.

Product Intent:
    The profile is the persistence layer for 'implicit memory'.  It is loaded
    at the start of every interaction (via the context window) and written
    back after the profile graph node updates it.  JSON storage ensures the
    profile survives server restarts for reliable demos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROFILES_PATH = Path(__file__).resolve().parents[2] / "mocks" / "user_profiles.json"

_DEFAULT_PROFILE: dict[str, Any] = {
    "preferred_brand": None,
    "budget_range": None,
    "interests": [],
    "travel_type": None,
    "com_style": None,
}


def _read_all() -> dict[str, dict[str, Any]]:
    """Read the entire profiles JSON file."""
    if not _PROFILES_PATH.exists():
        return {}
    with open(_PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_all(data: dict[str, dict[str, Any]]) -> None:
    """Write the entire profiles JSON file."""
    with open(_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_profile(user_id: str) -> dict[str, Any]:
    """Load a user profile, returning a default if it doesn't exist yet.

    Product Intent:
        Ensures every interaction starts with a valid profile — new users get
        a clean slate that will be populated implicitly over time.
    """
    all_profiles = _read_all()
    if user_id not in all_profiles:
        # Create a default profile for new users
        all_profiles[user_id] = dict(_DEFAULT_PROFILE)
        _write_all(all_profiles)
    return all_profiles[user_id]


def save_profile(user_id: str, profile: dict[str, Any]) -> None:
    """Persist a user profile to the JSON file.

    Product Intent:
        Called by the profile graph node at the end of every interaction so
        that the updated preferences are available for the next session.
    """
    all_profiles = _read_all()
    all_profiles[user_id] = profile
    _write_all(all_profiles)
