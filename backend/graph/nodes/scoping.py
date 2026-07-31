"""Scoping node — generates quick-tap buttons and text fields.

Product Intent:
    Instead of dumping all results at once, this node progressively narrows
    the user's intent using pre-designed (NOT AI-generated) buttons.  The
    digital vertical needs one round (button click); travel needs two (button
    click → text fields for dates/group size).

    For returning users with enough profile data (e.g., preferred brand),
    scoping is skipped entirely — the assistant goes straight to search.
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import AgentState
from mocks.llm_responses import SCOPING_BUTTONS, SCOPING_PROMPTS, TRAVEL_FIELDS


def _check_skip_scoping(state: AgentState) -> bool:
    """Return True if the profile already contains enough context to skip."""
    profile = state.get("profile", {})
    intent = state.get("intent")

    if intent == "digital" and profile.get("preferred_brand"):
        return True
    # Travel skip: if travel_type is already known
    if intent == "travel" and profile.get("travel_type"):
        return True
    return False


def scoping_node(state: AgentState) -> dict[str, Any]:
    """Generate scoping UI elements or process the user's selection.

    Product Intent:
        * Round 0 (first call): check profile for skip, then generate buttons.
        * Round 1 digital: process button click → go to search.
        * Round 1 travel: process trip-type button → generate text fields.
        * Round 2 travel: process dates/group size → go to search.
    """
    intent = state.get("intent", "general")
    scoping_round = state.get("scoping_round", 0)
    latest_msg = state["messages"][-1]["content"]
    selections: dict[str, Any] = dict(state.get("scoping_selections", {}))

    # --- Check skip-scoping on round 0 ---
    if scoping_round == 0 and _check_skip_scoping(state):
        profile = state.get("profile", {})
        if intent == "digital":
            selections["action"] = "Compare Models"  # default to compare
            selections["preferred_brand"] = profile.get("preferred_brand")
        if intent == "travel":
            selections["travel_type"] = profile.get("travel_type")
        return {
            "skip_scoping": True,
            "phase": "ready",
            "scoping_selections": selections,
        }

    # --- Round 0: generate buttons ---
    if scoping_round == 0:
        buttons = SCOPING_BUTTONS.get(intent, [])
        prompt = SCOPING_PROMPTS.get(intent, ["How would you like to refine your search?"])[0]
        return {
            "scoping_round": 1,
            "scoping_buttons": buttons,
            "scoping_fields": None,
            "phase": "scoping",
            "response": prompt,
        }

    # --- Round 1: user clicked a button ---
    if scoping_round == 1:
        if intent == "digital":
            # Process the button click directly → ready for search
            selections["action"] = latest_msg
            return {
                "scoping_selections": selections,
                "scoping_buttons": None,
                "phase": "ready",
            }

        if intent == "travel":
            # Process trip-type button → generate text fields (round 2)
            travel_type = latest_msg.replace(" Trip", "").strip()
            selections["travel_type"] = travel_type
            prompt = SCOPING_PROMPTS["travel"][1].format(travel_type=travel_type)
            return {
                "scoping_round": 2,
                "scoping_selections": selections,
                "scoping_buttons": None,
                "scoping_fields": TRAVEL_FIELDS,
                "phase": "scoping",
                "response": prompt,
            }

    # --- Round 2 (travel): user filled in text fields ---
    if scoping_round == 2 and intent == "travel":
        parts = [p.strip() for p in latest_msg.split(",")]
        if len(parts) >= 3:
            selections["group_size"] = parts[0]
            selections["start_date"] = parts[1]
            selections["end_date"] = parts[2]
        return {
            "scoping_selections": selections,
            "scoping_fields": None,
            "phase": "ready",
        }

    # Fallback (should not reach here in normal flow)
    return {"phase": "ready"}


def route_after_scoping(state: AgentState) -> str:
    """Conditional edge: go to profile (scoping, so profile updates) or search (ready)."""
    if state.get("phase") == "scoping":
        return "profile"
    return "search"
