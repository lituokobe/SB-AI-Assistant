"""Chat interface + quick-tap button rendering.

Product Intent:
    The chat interface is where the user converses with the assistant.  When
    the assistant returns scoping buttons or travel input fields, they appear
    below the chat — letting the user refine intent by clicking rather than
    typing.  This is the "guided narrowing" UX in action.
"""

from __future__ import annotations

import gradio as gr

from frontend.api_client import send_message

# Number of quick-tap buttons (max 3 per scoping round)
_NUM_BUTTONS = 3


async def handle_user_message(
    message: str,
    history: list[dict[str, str]],
    session_id: str,
    user_id: str,
):
    """Process a typed message and return updated UI state."""
    history.append({"role": "user", "content": message})

    response = await send_message(message, session_id, user_id)
    reply = response.get("response_text", "")
    history.append({"role": "assistant", "content": reply})

    return _build_ui_updates(response, history)


async def handle_button_click(
    button_label: str,
    history: list[dict[str, str]],
    session_id: str,
    user_id: str,
):
    """Process a quick-tap button click."""
    history.append({"role": "user", "content": button_label})

    response = await send_message(button_label, session_id, user_id)
    reply = response.get("response_text", "")
    history.append({"role": "assistant", "content": reply})

    return _build_ui_updates(response, history)


async def handle_travel_submit(
    group_size: str,
    start_date: str,
    end_date: str,
    history: list[dict[str, str]],
    session_id: str,
    user_id: str,
):
    """Process the travel field submission (round 2 scoping)."""
    combined = f"{group_size}, {start_date}, {end_date}"
    history.append({"role": "user", "content": combined})

    response = await send_message(combined, session_id, user_id)
    reply = response.get("response_text", "")
    history.append({"role": "assistant", "content": reply})

    return _build_ui_updates(response, history)


def _build_ui_updates(response: dict, history: list[dict[str, str]]):
    """Build the Gradio update tuple from an API response.

    Product Intent:
        Translates the structured API response into Gradio component updates:
        show/hide buttons, show/hide travel fields, update the profile sidebar.
        Uses ``gr.update()`` for every component to ensure consistent behaviour.
    """
    from frontend.components.sidebar import render_profile_html

    buttons = response.get("scoping_buttons")
    fields = response.get("scoping_fields")

    # Button visibility / label updates
    btn_updates: list[gr.update] = []
    for i in range(_NUM_BUTTONS):
        if buttons and i < len(buttons):
            btn_updates.append(gr.update(visible=True, value=buttons[i], interactive=True))
        else:
            btn_updates.append(gr.update(visible=False, value="", interactive=False))

    # Travel field visibility (group, start, end, submit — all toggle together)
    fields_visible = fields is not None
    field_updates = [gr.update(visible=fields_visible) for _ in range(4)]

    profile_html = render_profile_html(response.get("profile"))

    return (
        "",               # cleared textbox
        history,          # updated chat history
        btn_updates[0],   # btn1
        btn_updates[1],   # btn2
        btn_updates[2],   # btn3
        field_updates[0], # travel_group
        field_updates[1], # travel_start
        field_updates[2], # travel_end
        field_updates[3], # travel_submit
        profile_html,     # profile panel
    )


def build_no_change_outputs():
    """Return a tuple of gr.update() for when nothing should change.

    Used when the user sends an empty message.
    """
    return (
        gr.update(),
        gr.update(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(),
    )
