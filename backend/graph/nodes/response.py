"""Final response generation node.

Product Intent:
    Takes the guardrail-filtered product list and produces the natural-language
    recommendation that the user sees in the chat.  The tone is shaped by the
    user's communication-style preference (concise, casual, detailed) from the
    profile — this is "show, don't tell" in action.

    In production this would be an LLM call; here it uses deterministic
    templates from ``mocks/llm_responses.py``.
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import AgentState
from mocks.llm_responses import RESPONSE_TEMPLATES


def _format_product_digital(product: dict[str, Any]) -> str:
    """Format a digital product as a markdown card."""
    brand_str = f" **{product['brand']}** |" if product.get("brand") else ""
    specs_str = ""
    specs = product.get("specs", {})
    if specs:
        spec_parts = [f"{k.title()}: {v}" for k, v in specs.items()]
        specs_str = f"\n  📋 {' | '.join(spec_parts)}"

    return (
        f"📱 **{product['name']}** — {product['platform']}\n"
        f"  💰 ${product['price']:.0f} |{brand_str} 💸 {product['cashback_rate']:.0f}% cashback"
        f"{specs_str}"
    )


def _format_product_travel(product: dict[str, Any]) -> str:
    """Format a travel package as a markdown card."""
    hotel_str = f"\n  🏨 {product.get('hotel_name', 'Hotel TBD')}" if product.get("hotel_name") else ""
    dates_str = ""
    if product.get("start_date") and product.get("end_date"):
        dates_str = f"\n  📅 {product['start_date']} → {product['end_date']}"
    group_str = f"\n  👥 {product.get('group_size', '—')} travellers" if product.get("group_size") else ""

    return (
        f"✈️ **{product['name']}** — {product['platform']}\n"
        f"  💰 ${product['price']:.0f} | 💸 {product['cashback_rate']:.0f}% cashback"
        f"{hotel_str}{dates_str}{group_str}"
    )


def _format_products(products: list[dict[str, Any]], intent: str) -> str:
    """Format all products into a single markdown string."""
    if not products:
        return "_No products found matching your criteria._"

    if intent == "travel":
        cards = [_format_product_travel(p) for p in products]
    else:
        cards = [_format_product_digital(p) for p in products]
    return "\n\n".join(cards)


def generate_response(state: AgentState) -> dict[str, Any]:
    """Generate the assistant's textual reply from filtered products.

    Product Intent:
        Converts structured product data into a human-friendly message whose
        tone matches the user's profile, making the assistant feel personal
        rather than robotic.
    """
    intent = state.get("intent", "general")
    profile = state.get("profile", {})
    com_style = profile.get("com_style") or "formal"
    filtered_products = state.get("filtered_products", []) or []

    templates = RESPONSE_TEMPLATES.get(com_style, RESPONSE_TEMPLATES["formal"])
    template = templates.get(intent, templates["general"])

    if intent in ("digital", "travel"):
        products_str = _format_products(filtered_products, intent)
        response_text = template.format(products=products_str)
    else:
        response_text = template

    return {"response": response_text}


def route_after_response(state: AgentState) -> str:
    """Conditional edge: go to profile (normal) or END (com_style shortcut)."""
    if state.get("intent") == "com_style":
        return "__end__"
    return "profile"
