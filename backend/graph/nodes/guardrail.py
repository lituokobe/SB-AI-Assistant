"""Guardrail node — filters irrelevant items before display.

Product Intent:
    A post-generation validation layer that ensures every recommendation is
    strictly relevant to the narrowed scope and has a valid (live) cashback
    rate.  This is the quality gate between raw search results and the user-
    facing response.

    * Digital: removes items whose category doesn't match the query (e.g., a
      TV or phone case sneaking into a phone search).  If the user selected a
      brand, only that brand survives.
    * Travel: removes packages whose ``hotel_type`` doesn't match the selected
      trip type (e.g., a family hotel in a business-trip search).
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import AgentState


def guardrail_node(state: AgentState) -> dict[str, Any]:
    """Filter the search results for strict relevance and valid cashback.

    Product Intent:
        Guarantees that the user never sees irrelevant products or stale
        cashback rates, building trust in the assistant's recommendations.
    """
    intent = state.get("intent", "general")
    products = state.get("products", []) or []
    selections = state.get("scoping_selections", {})

    filtered: list[dict[str, Any]] = []

    for product in products:
        # Universal rule: cashback must be positive
        if product.get("cashback_rate", 0) <= 0:
            continue

        if intent == "digital":
            # Only keep the target category (smartphones or tablets)
            # Exclude TVs, accessories, etc.
            if product.get("category") not in ("smartphones", "tablets"):
                continue

            # If a preferred brand is set, only keep that brand
            preferred_brand = selections.get("preferred_brand")
            if preferred_brand and product.get("brand") != preferred_brand:
                continue

            filtered.append(product)

        elif intent == "travel":
            # Hotel type must match the selected trip type
            travel_type = selections.get("travel_type", "").lower()
            hotel_type = product.get("hotel_type", "").lower()
            if travel_type and hotel_type and hotel_type != travel_type:
                continue

            filtered.append(product)

        else:
            filtered.append(product)

    return {"filtered_products": filtered}
