"""HTTP endpoints — the FastAPI gateway.

Product Intent:
    Decouples the Gradio frontend from the LangGraph core.  Every request is
    validated against Pydantic V2 contracts, and responses carry the assistant
    reply alongside optional UI elements (scoping buttons, product cards) and
    the always-present user profile for the sidebar.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import get_user_profile, run_graph
from backend.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Product,
    ProfileResponse,
    ScopingField,
    UserProfile,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple health-check endpoint."""
    return HealthResponse()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a user message and return the assistant response.

    Product Intent:
        The single entry point for the conversational flow.  Depending on
        where the user is in the scoping journey, the response will contain
        scoping buttons, travel input fields, or final product recommendations.
    """
    state = run_graph(request.message, request.session_id, request.user_id)

    # Build optional scoping UI elements
    scoping_buttons: list[str] | None = state.get("scoping_buttons")
    scoping_fields_raw: list[dict] | None = state.get("scoping_fields")
    scoping_fields: list[ScopingField] | None = None
    if scoping_fields_raw:
        scoping_fields = [ScopingField(**f) for f in scoping_fields_raw]

    # Build optional product list
    filtered_products = state.get("filtered_products")
    products: list[Product] | None = None
    if filtered_products:
        products = [Product(**p) for p in filtered_products]

    # Build profile
    profile_data = state.get("profile", {})
    profile = UserProfile(**profile_data)

    return ChatResponse(
        response_text=state.get("response", ""),
        scoping_buttons=scoping_buttons,
        scoping_fields=scoping_fields,
        products=products,
        profile=profile,
    )


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str) -> ProfileResponse:
    """Fetch the current user profile for the sidebar."""
    profile_data = get_user_profile(user_id)
    return ProfileResponse(
        user_id=user_id,
        profile=UserProfile(**profile_data),
    )
