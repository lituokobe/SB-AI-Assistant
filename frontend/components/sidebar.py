"""The implicit user-profile display panel.

Product Intent:
    Renders the user profile in a sidebar that updates silently after every
    interaction.  The assistant NEVER says "I have updated your profile" --
    the user simply notices the data changing, which creates a sense of being
    understood without being intruded upon.
"""

from __future__ import annotations


def render_profile_html(profile: dict | None) -> str:
    """Return an HTML string rendering the user profile as a clean card.

    Product Intent:
        A polished, at-a-glance view of everything the assistant has learned
        about the user -- brand preferences, interests, travel type, and
        communication style.  Empty fields show a subtle dash to indicate
        "not yet known."  The profile is visible from first page load with
        all sections empty, so the user can watch it fill in over time.
    """
    if not profile:
        profile = {}

    brand = profile.get("preferred_brand") or "\u2014"
    budget = profile.get("budget_range") or "\u2014"
    interests = profile.get("interests") or []
    travel_type = profile.get("travel_type") or "\u2014"
    com_style = profile.get("com_style") or "\u2014"

    interests_badges = "".join(
        f"<span style='display:inline-block;background:#FF3407;color:#FFFFFF;"
        f"border-radius:12px;padding:3px 12px;margin:2px;font-size:12px;"
        f"font-family:Roboto,sans-serif;font-weight:700;'>{i}</span>"
        for i in interests
    ) if interests else "\u2014"

    # Resolve com_style display before the f-string (Python <3.12 disallows
    # backslash escapes inside f-string expression parts).
    em_dash = "\u2014"
    com_display = com_style.title() if com_style != em_dash else com_style

    return f"""
    <div style="font-family:Roboto,sans-serif;padding:16px;">
      <h3 style="margin:0 0 16px 0;color:#FF3407;font-family:Roboto,sans-serif;font-weight:900;">\U0001f464 User Profile</h3>
      <div style="background:#FFFFFF;border:2px solid #F39E8B;border-radius:12px;padding:16px;margin-bottom:8px;">
        <div style="margin-bottom:12px;">
          <span style="color:#000000;font-size:13px;font-weight:400;">Preferred Brand</span><br>
          <span style="font-size:16px;font-weight:700;color:#000000;">\U0001f3e2 {brand}</span>
        </div>
        <div style="margin-bottom:12px;">
          <span style="color:#000000;font-size:13px;font-weight:400;">Interests</span><br>
          <div style="margin-top:4px;">{interests_badges}</div>
        </div>
        <div style="margin-bottom:12px;">
          <span style="color:#000000;font-size:13px;font-weight:400;">Travel Type</span><br>
          <span style="font-size:16px;font-weight:700;color:#000000;">\u2708\ufe0f {travel_type}</span>
        </div>
        <div style="margin-bottom:12px;">
          <span style="color:#000000;font-size:13px;font-weight:400;">Budget Range</span><br>
          <span style="font-size:16px;font-weight:700;color:#000000;">\U0001f4b0 {budget}</span>
        </div>
        <div>
          <span style="color:#000000;font-size:13px;font-weight:400;">Communication Style</span><br>
          <span style="font-size:16px;font-weight:700;color:#000000;">\U0001f4ac {com_display}</span>
        </div>
      </div>
      <p style="color:#FF3407;font-size:11px;text-align:center;margin-top:12px;font-weight:400;">
        Profile updates silently \u2014 no explicit confirmation.<br>
        This panel is shown for demonstration purposes only;<br>
        in production, users would see only the chat area.
      </p>
    </div>
    """
