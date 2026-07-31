"""Pydantic V2 data contracts for all API requests, responses, and domain models.

Product Intent:
    These models define the strict boundary between the FastAPI gateway and the
    LangGraph core.  Every HTTP request and response is validated against these
    schemas, ensuring the frontend and backend never disagree on data shape.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Intent(str, Enum):
    """High-level intent categories determined by the router node."""

    DIGITAL = "digital"
    TRAVEL = "travel"
    COM_STYLE = "com_style"
    GENERAL = "general"


class ComStyle(str, Enum):
    """User's preferred communication tone, captured implicitly."""

    CONCISE = "concise"
    CASUAL = "casual"
    DETAILED = "detailed"


# ---------------------------------------------------------------------------
# Domain Models
# ---------------------------------------------------------------------------


class Product(BaseModel):
    """A single product or travel package returned by the search node.

    Digital products populate ``brand`` and ``specs``; travel packages
    populate ``destination``, ``hotel_type``, ``hotel_name``, dates and
    ``group_size``.
    """

    id: str
    name: str
    category: str
    brand: str | None = None
    price: float
    cashback_rate: float = Field(description="Cashback percentage, e.g. 8.0 = 8%")
    platform: str = Field(description="Merchant / platform name, e.g. 'Apple Store'")
    description: str = ""
    specs: dict[str, str] = Field(default_factory=dict)
    image_url: str | None = None

    # Travel-specific (None for digital products)
    destination: str | None = None
    hotel_type: str | None = None
    hotel_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    group_size: int | None = None


class UserProfile(BaseModel):
    """Persistent user profile, silently updated during conversations.

    This is the core of the 'implicit memory' feature — it is loaded at the
    start of every interaction (via the context window) and written back after
    the response is generated.
    """

    preferred_brand: str | None = None
    budget_range: str | None = None
    interests: list[str] = Field(default_factory=list)
    travel_type: str | None = None
    com_style: str | None = None


class ScopingField(BaseModel):
    """A single input field rendered during the second scoping round (travel)."""

    label: str
    field_type: str = Field(description="'number', 'date', or 'text'")


# ---------------------------------------------------------------------------
# API Contracts
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Inbound chat message from the Gradio frontend."""

    message: str
    session_id: str
    user_id: str = "default_user"


class ChatResponse(BaseModel):
    """Outbound response containing the assistant reply and optional UI elements.

    Depending on where the user is in the flow, exactly one of
    ``scoping_buttons``, ``scoping_fields``, or ``products`` will be set
    (alongside ``response_text``).
    """

    response_text: str
    scoping_buttons: list[str] | None = None
    scoping_fields: list[ScopingField] | None = None
    products: list[Product] | None = None
    profile: UserProfile


class ProfileResponse(BaseModel):
    """Standalone profile fetch for the sidebar (GET /profile)."""

    user_id: str
    profile: UserProfile


class HealthResponse(BaseModel):
    """Simple health-check payload."""

    status: str = "ok"
