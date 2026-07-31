"""Compiles the LangGraph nodes and edges into a runnable graph.

Product Intent:
    Wires together the six nodes (router, scoping, search, guardrail, response,
    profile) with conditional edges that implement the full product flow:

    * com_style shortcut:  router → profile → response → END
    * general:             router → response → profile → END
    * digital / travel:    router → scoping → (search → guardrail →
                           response → profile → END) or (END for more scoping)

    A MemorySaver checkpointer persists state across HTTP requests, keyed by
    ``thread_id = session_id``, enabling the multi-turn scoping loop.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.nodes.guardrail import guardrail_node
from backend.graph.nodes.profile import route_after_profile, update_profile
from backend.graph.nodes.response import generate_response, route_after_response
from backend.graph.nodes.router import route_after_router, router_node
from backend.graph.nodes.scoping import route_after_scoping, scoping_node
from backend.graph.nodes.search import search_node
from backend.graph.state import AgentState

# Singleton checkpointer shared across all sessions
_checkpointer = MemorySaver()


def build_graph():
    """Compile and return the runnable LangGraph agent.

    Product Intent:
        The graph is the heart of the agentic core — it encodes the product
        decision tree (route → scope → search → filter → respond → learn)
        as a state machine that persists across user turns.
    """
    builder = StateGraph(AgentState)

    # --- Register nodes ---
    builder.add_node("router", router_node)
    builder.add_node("scoping", scoping_node)
    builder.add_node("search", search_node)
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("response", generate_response)
    builder.add_node("profile", update_profile)

    # --- Edges ---
    # Entry: always start at the router
    builder.add_edge(START, "router")

    # After router: branch based on intent
    builder.add_conditional_edges("router", route_after_router, {
        "profile": "profile",
        "response": "response",
        "scoping": "scoping",
    })

    # After scoping: go to profile (to capture implicit signals) then END,
    # or proceed directly to search when scoping is complete.
    builder.add_conditional_edges("scoping", route_after_scoping, {
        "profile": "profile",
        "search": "search",
    })

    # Linear: search → guardrail → response
    builder.add_edge("search", "guardrail")
    builder.add_edge("guardrail", "response")

    # After response: go to profile (normal) or END (com_style shortcut)
    builder.add_conditional_edges("response", route_after_response, {
        END: END,
        "profile": "profile",
    })

    # After profile: go to response (com_style) or END (all others)
    builder.add_conditional_edges("profile", route_after_profile, {
        "response": "response",
        END: END,
    })

    return builder.compile(checkpointer=_checkpointer)


# Module-level singleton graph instance
graph = build_graph()
