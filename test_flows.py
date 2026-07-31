"""Integration test script — verifies all demo flows end-to-end.

Run with: uv run python test_flows.py
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

# --- Reset mock data to a clean state for deterministic tests ---
_profiles_path = Path(__file__).parent / "mocks" / "user_profiles.json"
_conversations_path = Path(__file__).parent / "mocks" / "conversations.json"
_profiles_path.write_text(json.dumps({
    "default_user": {
        "preferred_brand": None,
        "budget_range": None,
        "interests": [],
        "travel_type": None,
        "com_style": None,
    }
}, indent=2))
_conversations_path.write_text("[]")

client = TestClient(app)

print("=" * 60)
print("SB AI Assistant — Integration Tests")
print("=" * 60)

# --- 1. Health check ---
r = client.get("/health")
assert r.status_code == 200
print(f"\n[1] Health check: {r.json()}")

# --- 2. Digital flow ---
print("\n[2] Digital flow (phone with good camera)")

# Turn 1: user query → expect scoping buttons + profile updated with "Smartphones"
r = client.post("/chat", json={
    "message": "I need a phone with a good camera",
    "session_id": "test-digital",
})
assert r.status_code == 200
data = r.json()
print(f"  T1 response: {data['response_text']}")
print(f"  T1 buttons:  {data['scoping_buttons']}")
assert data["scoping_buttons"] == ["Look for a Brand", "Compare Models", "Find Max Cashback"]
assert data["products"] is None
# Profile should already have "Smartphones" after T1 (scoping → profile)
print(f"  T1 profile.interests: {data['profile']['interests']}")
assert "Smartphones" in data["profile"]["interests"], "Smartphones should be added after first message"

# Turn 2: click "Compare Models" → expect products
r = client.post("/chat", json={
    "message": "Compare Models",
    "session_id": "test-digital",
})
assert r.status_code == 200
data = r.json()
print(f"  T2 response (first 80): {data['response_text'][:80]}...")
print(f"  T2 products: {len(data['products']) if data['products'] else 0} items")
assert data["products"] is not None
assert len(data["products"]) > 0
# Guardrail should have filtered to smartphones only
for p in data["products"]:
    assert p["category"] in ("smartphones", "tablets"), f"Unexpected category: {p['category']}"
print(f"  T2 profile.interests: {data['profile']['interests']}")
assert "Smartphones" in data["profile"]["interests"]

# --- 3. Travel flow ---
print("\n[3] Travel flow (trip to Sydney)")

# Turn 1: user query → expect trip-type buttons, NO travel_type yet
r = client.post("/chat", json={
    "message": "I want to book a trip to Sydney",
    "session_id": "test-travel",
})
assert r.status_code == 200
data = r.json()
print(f"  T1 buttons: {data['scoping_buttons']}")
assert data["scoping_buttons"] == ["Family Trip", "Business Trip", "Leisure Trip"]
print(f"  T1 profile.travel_type: {data['profile']['travel_type']}")
assert data["profile"]["travel_type"] is None, "travel_type should not be set until user clicks a button"

# Turn 2: click "Business Trip" → expect text fields + travel_type updated
r = client.post("/chat", json={
    "message": "Business Trip",
    "session_id": "test-travel",
})
assert r.status_code == 200
data = r.json()
print(f"  T2 fields: {data['scoping_fields']}")
assert data["scoping_fields"] is not None
assert len(data["scoping_fields"]) == 3
print(f"  T2 profile.travel_type: {data['profile']['travel_type']}")
assert data["profile"]["travel_type"] == "Business", "travel_type should be 'Business' after clicking Business Trip"

# Turn 3: fill in fields → expect products
r = client.post("/chat", json={
    "message": "2, 2026-08-10, 2026-08-13",
    "session_id": "test-travel",
})
assert r.status_code == 200
data = r.json()
print(f"  T3 products: {len(data['products']) if data['products'] else 0} items")
assert data["products"] is not None
assert len(data["products"]) > 0
# Guardrail: only business hotels should remain
for p in data["products"]:
    assert p["hotel_type"] == "business", f"Unexpected hotel_type: {p['hotel_type']}"
    print(f"    - {p['name']} | {p['hotel_type']} | {p['cashback_rate']}% cashback")
print(f"  T3 profile.travel_type: {data['profile']['travel_type']}")
assert data["profile"]["travel_type"] == "Business"

# --- 4. Communication style flow ---
print("\n[4] Communication style flow")
r = client.post("/chat", json={
    "message": "Talk to me in a casual tone",
    "session_id": "test-comstyle",
})
assert r.status_code == 200
data = r.json()
print(f"  response: {data['response_text']}")
print(f"  profile.com_style: {data['profile']['com_style']}")
assert data["profile"]["com_style"] == "casual"
# Response should be in casual tone
assert "chill" in data["response_text"].lower() or "casual" in data["response_text"].lower()

# --- 5. General flow ---
print("\n[5] General flow (greeting)")
r = client.post("/chat", json={
    "message": "Hello there",
    "session_id": "test-general",
})
assert r.status_code == 200
data = r.json()
print(f"  response: {data['response_text'][:80]}...")

# --- 6. Find Max Cashback flow ---
print("\n[6] Digital flow — Find Max Cashback")
r = client.post("/chat", json={
    "message": "I need a phone",
    "session_id": "test-cashback",
})
data = r.json()
assert data["scoping_buttons"] is not None

r = client.post("/chat", json={
    "message": "Find Max Cashback",
    "session_id": "test-cashback",
})
data = r.json()
print(f"  Products (sorted by cashback desc):")
prev_rate = float("inf")
for p in data["products"]:
    print(f"    - {p['name']} | {p['cashback_rate']}%")
    assert p["cashback_rate"] <= prev_rate, "Products not sorted by cashback desc"
    prev_rate = p["cashback_rate"]
assert "Cashback" in data["profile"]["interests"], "Cashback interest should be added after clicking Find Max Cashback"

# --- 7. Guardrail filtering ---
print("\n[7] Guardrail filtering — no TVs or accessories in phone results")
for p in data["products"]:
    assert p["category"] != "tvs", "TV found in phone results!"
    assert p["category"] != "accessories", "Accessory found in phone results!"
print("  No TVs or accessories in results.")

# --- 8. Formal tone verification ---
print("\n[8] Formal tone — all responses before com_style change use formal tone")
# Fresh profile to verify default formal tone
_profiles_path.write_text(json.dumps({
    "default_user": {
        "preferred_brand": None,
        "budget_range": None,
        "interests": [],
        "travel_type": None,
        "com_style": None,
    }
}, indent=2))
r = client.post("/chat", json={
    "message": "Hi",
    "session_id": "test-formal",
})
data = r.json()
print(f"  Response: {data['response_text']}")
assert "Welcome" in data["response_text"] or "welcome" in data["response_text"].lower(), \
    "Default tone should be formal"

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)

# --- Final reset for clean demo state ---
_profiles_path.write_text(json.dumps({
    "default_user": {
        "preferred_brand": None,
        "budget_range": None,
        "interests": [],
        "travel_type": None,
        "com_style": None,
    }
}, indent=2))
_conversations_path.write_text("[]")
print("\nMock data reset for clean demo state.")
