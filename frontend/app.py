"""Main Gradio launch script -- the SB AI Assistant UI.

Product Intent:
    Assembles the chat interface, quick-tap scoping buttons, travel input
    fields, and the implicit profile sidebar into a single-page app.  The
    frontend talks exclusively to the FastAPI backend via HTTP -- it never
    touches LangGraph directly.

    All styling uses the ShopBack company colour scheme (#FF3407, #F39E8B,
    #000000, #FFFFFF) and Roboto font family.

Run with:
    uv run python frontend/app.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Ensure the project root is on sys.path so that `from frontend...` imports
# work when running `python frontend/app.py` directly.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import gradio as gr

from frontend.components.chatbot import (
    build_no_change_outputs,
    handle_button_click,
    handle_travel_submit,
    handle_user_message,
)
from frontend.components.sidebar import render_profile_html

# Session IDs are generated per browser session via gr.State inside
# build_app(), so each visitor gets an isolated profile — critical for
# HF Spaces where multiple users share the same process.

# ---------------------------------------------------------------------------
# Company-branded CSS (ShopBack colour scheme + Roboto font)
# ---------------------------------------------------------------------------
_CUSTOM_CSS = """
/* ---- Roboto font ---- */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');

/* ---- Global font + text colour ---- */
* { font-family: 'Roboto', sans-serif !important; }
p, span, div, label { color: #000000 !important; }

/* ---- Headers ---- */
h1 { color: #FF3407 !important; font-weight: 900 !important; }
h2, h3 { color: #000000 !important; font-weight: 700 !important; }

/* ---- Scoping button row (close to chatbot, gap before input) ---- */
.scoping-row { margin-top: -12px !important; margin-bottom: 4px !important; padding: 8px 12px !important; }
.scoping-row .form { background: transparent !important; border: none !important; box-shadow: none !important; }
.travel-row { margin-top: -8px !important; margin-bottom: 4px !important; padding: 8px 12px !important; }

/* ---- Input bar (text field + send button, side by side) ---- */
.input-bar {
    margin-top: 20px !important;
    padding: 0 !important;
    gap: 8px !important;
    align-items: center !important;
}
.input-bar .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.input-bar input[type="text"] {
    border: 1px solid #ccc !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    background: #FFFFFF !important;
    height: 48px !important;
}
.input-bar button {
    border-radius: 8px !important;
    margin: 0 !important;
    padding: 12px 24px !important;
    height: 48px !important;
    font-size: 15px !important;
}

/* ---- Chatbot user message bubbles ---- */
#chatbot .message.user,
#chatbot [data-testid="user"],
#chatbot .user.bubble {
    background-color: #FF3407 !important;
    border-color: #FF3407 !important;
}
#chatbot .message.user *,
#chatbot [data-testid="user"] *,
#chatbot .user.bubble * {
    color: #FFFFFF !important;
}

/* ---- Chatbot assistant message bubbles ---- */
#chatbot .message.bot,
#chatbot [data-testid="bot"],
#chatbot .bot.bubble {
    background-color: #F39E8B !important;
    border-color: #F39E8B !important;
}
#chatbot .message.bot *,
#chatbot [data-testid="bot"] *,
#chatbot .bot.bubble * {
    color: #000000 !important;
}

/* ---- Scoping buttons: different colour per purpose ---- */
/* Button 1 -- salmon (secondary action) */
.sb-btn-salmon button {
    background-color: #F39E8B !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
.sb-btn-salmon button:hover {
    background-color: #E8876B !important;
}

/* Button 2 -- brand red (primary action) */
.sb-btn-red button {
    background-color: #FF3407 !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
.sb-btn-red button:hover {
    background-color: #D62A00 !important;
}

/* Button 3 -- black (high emphasis) */
.sb-btn-black button {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
.sb-btn-black button:hover {
    background-color: #333333 !important;
}

/* ---- Text input border accent ---- */
input[type="text"]:focus, textarea:focus {
    border-color: #FF3407 !important;
    box-shadow: 0 0 0 2px rgba(255, 52, 7, 0.2) !important;
}

/* ---- Chatbot border ---- */
#chatbot { border: 2px solid #F39E8B !important; border-radius: 12px !important; }
"""


def build_app() -> gr.Blocks:
    """Construct and return the Gradio Blocks UI."""
    with gr.Blocks(title="SB AI Assistant") as app:
        gr.Markdown("# SB AI Assistant")
        gr.Markdown("_Your personalised shopping companion -- guided narrowing + implicit memory_")

        with gr.Row():
            # --- Left column: chat + inputs ---
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=450,
                    elem_id="chatbot",
                )

                # Quick-tap scoping buttons (initially hidden).
                # Each button has a distinct company colour via elem_classes.
                with gr.Row(elem_classes="scoping-row"):
                    btn1 = gr.Button("", visible=False, elem_classes="sb-btn-salmon")
                    btn2 = gr.Button("", visible=False, elem_classes="sb-btn-red")
                    btn3 = gr.Button("", visible=False, elem_classes="sb-btn-black")

                # Travel input fields (initially hidden)
                with gr.Row(elem_classes="travel-row"):
                    travel_group = gr.Textbox(label="Group size", visible=False, scale=1)
                    travel_start = gr.Textbox(label="Start date (YYYY-MM-DD)", visible=False, scale=1)
                    travel_end = gr.Textbox(label="End date (YYYY-MM-DD)", visible=False, scale=1)
                    travel_submit = gr.Button("Submit", visible=False, scale=1, elem_classes="sb-btn-black")

                # Main text input — unified bar (no label, field + button flush)
                with gr.Row(elem_classes="input-bar"):
                    msg_input = gr.Textbox(
                        scale=5,
                        container=False,
                    )
                    send_btn = gr.Button("Send", scale=1, elem_classes="sb-btn-red", min_width=80)

            # --- Right column: profile sidebar ---
            with gr.Column(scale=1):
                profile_panel = gr.HTML(
                    value=render_profile_html({}),
                    label="User Profile",
                )

        # Per-session UUID — each browser session gets a unique ID,
        # so the profile is isolated per visitor (critical for HF Spaces
        # where multiple users share the same process).
        session_state = gr.State(value=lambda: str(uuid.uuid4()))

        # --- Output list (order matters!) ---
        outputs = [
            msg_input, chatbot, btn1, btn2, btn3,
            travel_group, travel_start, travel_end, travel_submit,
            profile_panel,
        ]

        # --- Event handlers ---

        async def on_send(message, history, session_id):
            """Handle typed message submission."""
            if not message.strip():
                return build_no_change_outputs()
            return await handle_user_message(message, history, session_id, session_id)

        async def on_btn1_click(btn_val, history, session_id):
            """Handle quick-tap button 1."""
            return await handle_button_click(btn_val, history, session_id, session_id)

        async def on_btn2_click(btn_val, history, session_id):
            """Handle quick-tap button 2."""
            return await handle_button_click(btn_val, history, session_id, session_id)

        async def on_btn3_click(btn_val, history, session_id):
            """Handle quick-tap button 3."""
            return await handle_button_click(btn_val, history, session_id, session_id)

        async def on_travel_submit(group, start, end, history, session_id):
            """Handle travel field submission."""
            return await handle_travel_submit(group, start, end, history, session_id, session_id)

        # Wire up events -- pass button component as input to get current label
        send_btn.click(on_send, [msg_input, chatbot, session_state], outputs)
        msg_input.submit(on_send, [msg_input, chatbot, session_state], outputs)

        btn1.click(on_btn1_click, [btn1, chatbot, session_state], outputs)
        btn2.click(on_btn2_click, [btn2, chatbot, session_state], outputs)
        btn3.click(on_btn3_click, [btn3, chatbot, session_state], outputs)

        travel_submit.click(
            on_travel_submit,
            [travel_group, travel_start, travel_end, chatbot, session_state],
            outputs,
        )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, css=_CUSTOM_CSS)
