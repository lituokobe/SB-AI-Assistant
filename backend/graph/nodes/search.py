"""Search node — queries the mock product database.

Product Intent:
    Retrieves products from ``mocks/products.json`` based on the intent and
    scoping selections.  This simulates a search engine call — in production
    it would query SB's merchant/cashback database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.graph.state import AgentState

_PRODUCTS_PATH = Path(__file__).resolve().parents[3] / "mocks" / "products.json"


def _load_products() -> list[dict[str, Any]]:
    """Load all mock products from the JSON file."""
    with open(_PRODUCTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _search_digital(selections: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch digital products based on scoping selections.

    Product Intent:
        * "Look for a Brand" → return phones grouped by brand.
        * "Compare Models" → return all phones for comparison; if a preferred
          brand exists in the profile, filter to that brand.
        * "Find Max Cashback" → return phones sorted by cashback (descending).
    """
    all_products = _load_products()
    action = selections.get("action", "")
    preferred_brand = selections.get("preferred_brand") or profile.get("preferred_brand")

    # Determine the target category from the original query
    # Default to smartphones; "tablet" keyword switches to tablets
    category = "smartphones"

    phones = [p for p in all_products if p["category"] == category]

    # Also include tablets if the query mentions tablets
    # (checked via the profile interests or original message)
    if "tablets" in profile.get("interests", []):
        tablets = [p for p in all_products if p["category"] == "tablets"]
        phones.extend(tablets)

    if action == "Find Max Cashback":
        phones = sorted(phones, key=lambda p: p["cashback_rate"], reverse=True)
    elif action == "Compare Models":
        if preferred_brand:
            phones = [p for p in phones if p.get("brand") == preferred_brand]
    elif action == "Look for a Brand":
        # Return all phones so user can see brand options
        pass

    return phones


def _search_travel(selections: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch travel packages based on scoping selections."""
    all_products = _load_products()
    destination = selections.get("destination")
    travel_type = selections.get("travel_type", "").lower()

    results = [
        p for p in all_products
        if p["category"] == "travel"
        and (destination is None or p.get("destination") == destination)
    ]

    # Attach dates and group size from selections
    start_date = selections.get("start_date")
    end_date = selections.get("end_date")
    group_size = selections.get("group_size")
    for r in results:
        if start_date:
            r["start_date"] = start_date
        if end_date:
            r["end_date"] = end_date
        if group_size:
            r["group_size"] = int(group_size) if str(group_size).isdigit() else group_size

    return results


def search_node(state: AgentState) -> dict[str, Any]:
    """Query mock products based on intent and scoping selections.

    Product Intent:
        Bridges the gap between the user's narrowed intent and SB's product
        catalogue.  Returns raw results that the guardrail node will filter.
    """
    intent = state.get("intent", "general")
    selections = state.get("scoping_selections", {})
    profile = state.get("profile", {})

    if intent == "digital":
        products = _search_digital(selections, profile)
    elif intent == "travel":
        products = _search_travel(selections)
    else:
        products = []

    return {"products": products}
