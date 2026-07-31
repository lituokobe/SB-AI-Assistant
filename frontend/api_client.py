"""Async HTTPX wrapper to call the FastAPI backend.

Product Intent:
    The frontend MUST NOT talk directly to LangGraph — it goes through the
    FastAPI gateway via HTTP.  This module provides a thin async client that
    the Gradio components use for every interaction.
"""

from __future__ import annotations

import httpx

BACKEND_URL = "http://localhost:8000"


async def send_message(message: str, session_id: str, user_id: str = "default_user") -> dict:
    """Send a chat message to the backend and return the response dict.

    Product Intent:
        Maps each user action (typing, button click, field submission) to a
        single POST /chat call.  The response carries the assistant reply,
        optional scoping UI elements, optional product cards, and the updated
        profile for the sidebar.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "session_id": session_id,
                "user_id": user_id,
            },
        )
        response.raise_for_status()
        return response.json()


async def fetch_profile(user_id: str = "default_user") -> dict:
    """Fetch the current user profile from the backend."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BACKEND_URL}/profile/{user_id}")
        response.raise_for_status()
        return response.json()
