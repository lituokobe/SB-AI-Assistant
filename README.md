# SB Shopping Platform AI Assistant

**An Agentic AI Shopping Companion Prototype**  
*Built for the Product Lead, AI-Native (Special Projects) Role*

## Context & Vision
This prototype was built to address two core friction points in modern AI e-commerce assistants:
1. **Cognitive Overload:** Users are presented with overly broad, un-scoped search results (e.g., dumping a user on a merchant's homepage instead of deep-linking to the exact product).
2. **Stateless Amnesia:** Assistants forget user preferences between sessions, forcing users to repeatedly input constraints.

The **SB AI Assistant** shifts the paradigm from a "passive search directory" to an "active, personalized shopping companion." It uses **progressive disclosure** (via pre-designed quick-action buttons) to narrow user intent, and **harness engineering** to implicitly adapt to user preferences over time without being intrusive.

---

## Core Product Features

*   **Vertical-Specific Guided Narrowing:** Instead of returning a wall of links, the assistant routes queries (Digital vs. Travel) and presents pre-designed UI buttons (e.g., `[Look for a Brand]`, `[Family Trip]`) to narrow the scope in a maximum of 2 clicks.
*   **Implicit User Profiling:** The system passively updates a user profile based on interactions (e.g., noting a preference for Apple products). This profile silently shapes future responses ("show, don't tell"), skipping unnecessary scoping questions for returning users.
*   **Post-Generation Guardrails:** A deterministic validation layer ensures that AI-generated recommendations are strictly relevant to the narrowed scope and verified against live (mocked) cashback rates before display.

---

## Architecture

To simulate a production-grade environment, this prototype strictly separates the UI, the API gateway, and the agentic logic.

```text
[ Gradio Frontend ] <== HTTP/JSON ==> [ FastAPI Gateway ] <== State ==> [ LangGraph Core ] <== Read ==> [ Mock Data ]
```

- **Frontend (Gradio)**: Handles the conversational UI, rendering quick-tap buttons, and displaying the implicit user profile sidebar.
- **API Gateway (FastAPI)**: Enforces strict Pydantic V2 contracts for all requests and responses. Decouples the frontend from the agent implementation. Manages session IDs and passes them to the LangGraph checkpointer.
- **Agentic Core (LangGraph)**: Manages the state machine, intent routing, scoping logic, guardrails, and profile updates.
- **Mock Data Layer**: Simulates LLM outputs and SB's proprietary merchant/cashback database to ensure deterministic, reliable demos without external API dependencies.

### Node Pipeline

```text
START → [router] ─── classifies intent (digital | travel | com_style | general)
                 │
                 ├── com_style ──────────────► [profile] ──► END
                 │
                 ├── digital / travel ──► [scoping] ──► [search] ──► [guardrail] ──► [response] ──► [profile] ──► END
                 │
                 └── general ──────────────► [response] ──► [profile] ──► END
```

Key behaviours:
- **Scoping is iterative:** the Travel flow requires two rounds (buttons → text fields).
- **Skip-scoping:** if the user profile already contains enough context (e.g., preferred brand), scoping is skipped.
- **Profile read/write:** the profile is read at the start (context assembly) and written at the end (after response).

## Tech Stack
- **Language:** Python 3.13
- **Package Manager:** uv (Ultra-fast Python package installer and resolver)
- **Agentic Framework:** LangChain / LangGraph
- **Backend API:** FastAPI, Uvicorn
- **Frontend UI:** Gradio
- **Data Validation:** Pydantic V2
- **HTTP Client:** HTTPX (for async frontend-to-backend communication)

## Getting Started

### Prerequisites

Ensure you have Python 3.13+ and `uv` installed.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run the Backend (FastAPI + LangGraph)
Open your first terminal and start the API server on port 8000:

```bash
uv run uvicorn backend.main:app --reload --port 8000
```
*(You can view the auto-generated API docs at `http://localhost:8000/docs`)*

### 3. Run the Frontend (Gradio)
Open a second terminal and launch the UI:
```bash
uv run python frontend/app.py
```
The Gradio app will start, usually on `http://localhost:7860`. Open this URL in your browser.

## Demo Scenarios to Try
Once the app is running, try these scenarios to experience the product logic:

### Scenario 1: The Digital Shopper (Guided Narrowing)
1. Type: *"I want to buy a phone with a good camera."*
2. Observe the assistant routing to the Digital vertical and presenting scoping buttons. 
3. Click `[Compare Models]`. 
4. Observe the final, highly focused product recommendations with verified cashback rates.

### Scenario 2: The Travel Planner (Multi-Round Scoping)
1. Type: *"I need to plan a trip to Tokyo."*
2. Observe the assistant routing to the Travel vertical and presenting scoping buttons (e.g., `[Family Trip]`, `[Business Trip]`).
3. Click `[Business Trip]`.
4. Observe the second scoping round: text fields for travel group size and dates.
5. Fill in the details and observe flight/hotel combinations with cashback rates from multiple platforms.

### Scenario 3: Implicit Memory (Harness Engineering)
1. Complete Scenario 1. 
2. Look at the **User Profile Sidebar** on the right. Notice how it silently updated to reflect your interest in "Smartphones" and your preferred brand.
3. Start a new chat and type: *"What about a tablet?"*
4. Observe how the assistant **skips the brand-selection button** (because your preferred brand is already known) and directly presents relevant tablet recommendations.
5. Notice how the response tone matches your communication-style preference — without the assistant ever saying "I remember you."

### Scenario 4: Communication Style
1. Type: *"Please talk to me in a casual tone."*
2. Observe the assistant acknowledging the change in a casual tone.
3. Look at the **User Profile Sidebar** — notice "Communication style: casual" has been added silently.
4. In subsequent interactions, observe how all responses adopt the casual tone automatically.
