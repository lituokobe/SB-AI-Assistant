"""Hugging Face Spaces entry point (Gradio SDK).

Product Intent:
    When deploying to Hugging Face Spaces with the Gradio SDK, only a single
    process is allowed.  This file starts the FastAPI backend in a background
    thread, waits for it to be ready, and then launches the Gradio frontend —
    preserving the architectural separation (frontend → HTTP → backend → graph)
    without requiring a Docker container.

    For local development, continue running the two processes separately:
        Terminal 1: uv run uvicorn backend.main:app --reload --port 8000
        Terminal 2: uv run python frontend/app.py
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

# Ensure the project root is on sys.path so that all package imports work.
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import httpx
import uvicorn

from frontend.app import _CUSTOM_CSS, build_app

# --- HF Spaces ZeroGPU compatibility ---------------------------------------
# HF Spaces with ZeroGPU hardware auto-installs the `spaces` package and
# requires at least one @spaces.GPU decorated function at module level.
# This no-op placeholder satisfies that check without requesting GPU
# resources.  On CPU hardware or local development, `spaces` is not
# installed, so the import is optional.
try:
    import spaces

    @spaces.GPU
    def _zero_gpu_placeholder() -> None:
        """Satisfy HF Spaces ZeroGPU startup check without using GPU."""
        pass
except ImportError:
    pass


def _start_backend() -> None:
    """Start the FastAPI backend in a background daemon thread."""
    config = uvicorn.Config(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    server.run()


# --- Launch sequence --------------------------------------------------------

# 1. Start the FastAPI backend in the background.
backend_thread = threading.Thread(target=_start_backend, daemon=True)
backend_thread.start()

# 2. Wait for the backend health endpoint to respond (max 30 seconds).
for _attempt in range(30):
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=1.0)
        if resp.status_code == 200:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("WARNING: Backend not ready after 30s — starting Gradio anyway.")

# 3. Launch the Gradio frontend on the port HF Spaces expects (7860).
app = build_app()
app.launch(server_name="0.0.0.0", server_port=7860, css=_CUSTOM_CSS)
