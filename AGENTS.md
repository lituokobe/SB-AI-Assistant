# AI Coding Assistant Rules

## Role & Context
You are an expert Python 3.13 Full-Stack Engineer building a prototype to solve problems of an existing product. 
The project is an AI shopping assistant prototype for SB, a shopping cashback platform that connects users to products/e-commerce platforms across multiple categories with a various types of cashback bonuses.

## STRICT CONSTRAINTS
1. NO REAL LLM API CALLS. Do not use OpenAI, Anthropic, or any external LLM APIs. All "LLM" outputs must be mocked using the `mocks/` directory or hardcoded logic.
2. Package Management: Use `uv` for all dependency management.
3. Typing: Use strict Python type hinting. Use Pydantic V2 for all API contracts and data validation. Use `TypedDict` for LangGraph state.
4. Async: Use `async/await` for FastAPI routes and HTTP clients.
5. Determinism: All mock data and mock logic must be deterministic. The same input must always produce the same output so demos are reproducible.

## Architecture Rules
- The Frontend (Gradio) MUST NOT talk directly to LangGraph. It must call the FastAPI backend via HTTP.
- FastAPI handles the API contracts and state management.
- LangGraph handles the agentic routing, scoping, and guardrails.
- Separation of Concerns: Keep UI logic in `frontend/`, business logic in `backend/graph/`, and data contracts in `backend/models.py`.

## Graph Flow (Node Pipeline)
The LangGraph state machine processes each user turn through the following pipeline:

```text
START
  │
  ▼
[router] ─── classifies intent (digital | travel | com_style | general)
  │
  ├── com_style ──────────────────────────► [profile] ──────────► END
  │
  ├── digital / travel ──► [scoping] ──► (returns buttons / text fields to user)
  │                              │
  │                              ▼  (next user turn: button click or input)
  │                          [scoping]  (round 2, if needed — e.g. travel dates)
  │                              │
  │                              ▼
  │                           [search] ──► [guardrail] ──► [response] ──► [profile] ──► END
  │
  └── general ──────────────────────────► [response] ──► [profile] ──► END
```

Key behaviours:
- **Scoping is iterative.** The Travel flow requires two rounds (trip-type buttons -> date/group-size fields). The state tracks the current scoping round. The graph returns to the user after each round — it does not block or wait.
- **Skip-scoping for returning users.** The `scoping` node checks the user profile first. If enough is known (e.g., `preferred_brand` is set), scoping is skipped and the flow goes directly to `search`.
- **Communication style is a shortcut.** The `com_style` intent bypasses the entire search pipeline (router -> profile -> END).
- **Profile is read at the start, written at the end.** The context window (profile + summary + last 3 conversations) is assembled before routing. The profile is updated after the response is generated.

## State Management
The scoping flow spans multiple user turns (type query -> get buttons -> click button -> get results). Each user action is a separate HTTP request to the FastAPI backend. The LangGraph state must persist between calls.

- Use LangGraph's `MemorySaver` checkpointer, keyed by `thread_id = session_id`.
- The checkpointer is configured in `backend/graph/builder.py`.
- The FastAPI dependency layer (`backend/api/dependencies.py`) manages session IDs and passes them to the graph runner.
- The state (`backend/graph/state.py`) tracks: intent, scoping round, accumulated selections, conversation messages, and the user profile.

## Memory Layer
The `backend/memory/` directory is a data-access layer (storage and retrieval). It does NOT contain business logic — that lives in `backend/graph/nodes/`.

| Module | Responsibility |
|---|---|
| `memory/profile.py` | User profile CRUD (load, save, mutate fields). |
| `memory/history.py` | Conversation history storage (last 3 per user) + session summary generation. |
| `memory/context.py` | Context window assembly: combines profile + summary + last 3 conversations into a single context dict for the graph. |

The context window is assembled at the start of every interaction and passed into the graph state. This is the "harness engineering" approach: the structured profile, a summary of historical chats, and the most recent three conversations form the context for every future interaction.

## Coding Style
- Write clean, modular, and highly readable code.
- Add docstrings to all functions explaining the "Product Intent" behind the code.
- Use modern Python 3.13 features where applicable.
