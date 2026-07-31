"""FastAPI entrypoint — starts the API gateway.

Product Intent:
    The API gateway sits between the Gradio frontend and the LangGraph core.
    It enforces Pydantic V2 contracts, manages session state, and exposes
    auto-generated docs at /docs for easy demo walkthroughs.

    Run with:
        uv run uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router

app = FastAPI(
    title="SB AI Assistant",
    description="Agentic AI shopping companion — guided narrowing + implicit profiling",
    version="0.1.0",
)

# Allow the Gradio frontend to call this API.
# Wildcard origin supports both local dev and Hugging Face Spaces deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
