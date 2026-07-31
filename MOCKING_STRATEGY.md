# Mocking Strategy (How to fake the AI)

Since this is a UI/UX and architecture prototype, we do not have API keys. You must simulate LLM behavior deterministically. **The same input must always produce the same output** so demos are reproducible.

## 1. Simulating LLM Nodes in LangGraph
Instead of calling an LLM, nodes use conditional logic or read from `mocks/llm_responses.py`.
- Example for `router` node: 
  ```python
  def route_intent(state: State) -> str:
      user_input = state["messages"][-1].content.lower()
      if "phone" in user_input or "camera" in user_input:
          return "digital"
      elif "trip" in user_input or "flight" in user_input:
          return "travel"
      elif "tone" in user_input or "talk to me" in user_input:
          return "com_style"
      return "general"
  ```

## 2. Simulating the "Scoping" Output
When the graph needs to ask a scoping question, return a structured Pydantic model containing the text and the buttons/text fields.

- Example (round 1 — buttons): 
  ```json
  {
      "text": "How would you like to narrow down your phone search?",
      "buttons": ["Look for a Brand", "Compare Models", "Find Max Cashback"]
  }
  ```

- Example (round 2 — text fields, travel flow only):
  ```json
  {
      "text": "Got it — a business trip! Just a few details:",
      "fields": [
          {"label": "Travel group size", "type": "number"},
          {"label": "Starting date", "type": "date"},
          {"label": "End date", "type": "date"}
      ]
  }
  ```

### Skip-Scoping for Returning Users
The `scoping` node must check the user profile *before* generating buttons. If enough is already known, skip scoping entirely and go straight to `search`.
- Example:
  ```python
  def scope(state: State) -> State:
      profile = state["profile"]
      if profile.get("preferred_brand") and state["intent"] == "digital":
          # User already has a brand preference — skip scoping
          state["skip_scoping"] = True
          return state
      # Otherwise, generate scoping buttons based on intent
      ...
  ```

### Multi-Round Scoping (Travel Flow)
The Travel flow requires two scoping rounds. The state tracks `scoping_round`:
- **Round 1:** return trip-type buttons ([Family Trip], [Business Trip], [Leisure Trip]).
- **Round 2:** return text fields ([travel group size], [starting date], [end date]).
- After round 2, the flow proceeds to `search`.

## 3. Simulating the "Guardrail"
The guardrail node receives a list of mock products. It must iterate through them and remove any product not suitable, e.g, `category != "smartphones"`, `hotel_type != "family"`.

## 4. Simulating the "Response" Generation
The `response` node takes filtered products and produces the assistant's textual reply. This is an "LLM output" that must be mocked using templates from `mocks/llm_responses.py`.
- Example:
  ```python
  def generate_response(state: State) -> State:
      products = state["filtered_products"]
      tone = state["profile"].get("com_style", "concise")
      template = RESPONSE_TEMPLATES[tone]  # from mocks/llm_responses.py
      state["response"] = template.format(products=products)
      return state
  ```

## 5. Simulating Memory / Profile Updates
Create a `UserProfile` Pydantic model. When the user interacts, use simple keyword extraction to update the profile silently.
- Example: 
  - If user clicks "Compare Models" on an iPhone query, update `profile.preferred_brand = "Apple"`.
  - If user clicks "Business Trip" on a travel query, update `profile.travel_type = "Business"`.
  - If user says "Talk to me in casual tone", update `profile.com_style = "Casual"`.

## 6. Simulating Session Summaries
After each session, generate a short auto-conclusion that captures durable preferences. This summary is stored via `memory/history.py` and included in future context windows.
- Example:
  ```python
  def generate_session_summary(conversation: dict) -> str:
      # Mocked: keyword-based extraction, no LLM call
      if "camera" in conversation["user_input"]:
          return "User prioritises camera quality when choosing phones."
      return "User explored general product options."
  ```

## 7. Conversation History Storage
Conversation history (the last 3 conversations per user) must persist across API calls. For demo reliability across server restarts, use a JSON file.
- Storage location: `mocks/conversations.json` (or an in-memory dict if persistence across restarts is not needed).
- Retention policy: keep only the 3 most recent conversations per user; evict older ones.
- The context window assembled by `memory/context.py` reads from this store.
