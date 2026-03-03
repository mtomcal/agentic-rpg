# Ralph A — Backend Plan

## Overview

Build the entire Python/FastAPI backend in 6 sequential phases using red/green TDD. Each phase writes failing tests first, then implements the minimum code to pass. Best effort — ugly is fine, working is required.

**Stack**: Python 3.12+, FastAPI, uvicorn, uv, Pydantic v2, asyncpg, Alembic, LangChain, LangGraph, LangSmith, pytest, Docker Compose, PostgreSQL.

**Key constraint**: Every phase must leave `uv run pytest` passing before moving on.

---

## Phase 1: Scaffold + Docker Compose + Postgres + All Pydantic Models

### Goal
Set up the full project structure, Docker Compose environment, database, and every Pydantic model defined across all specs.

### Steps

1. Create `backend/` directory with `pyproject.toml` using `uv`:
   - Dependencies: fastapi, uvicorn, pydantic, pydantic-settings, asyncpg, alembic, langchain-core, langchain-anthropic, langgraph, pytest, pytest-asyncio, httpx, structlog
   - Project name: `agentic-rpg`
   - Source layout: `backend/src/agentic_rpg/`

2. Create the full directory structure per `docs/tech/python-backend.md`:
   ```
   backend/src/agentic_rpg/
     __init__.py, main.py, config.py, db.py
     api/ (routes.py, handlers.py, websocket.py, middleware.py, dependencies.py)
     agent/ (graph.py, context.py, prompt.py)
     tools/ (registry.py, character.py, inventory.py, world.py, narrative.py)
     state/ (manager.py, migrations.py)
     events/ (bus.py, schemas.py)
     models/ (game_state.py, character.py, inventory.py, world.py, story.py, events.py, api.py)
     llm/ (client.py, types.py)
   backend/tests/ (conftest.py, test_models/, test_state/, test_events/, test_tools/, test_agent/, test_api/)
   backend/alembic/ (env.py, versions/)
   backend/alembic.ini
   ```

3. Create `docker-compose.yml` at project root:
   - `postgres` service: postgres:16, port 5432, volume for data, health check
   - `backend` service: build from `backend/`, port 8080, depends_on postgres, env vars for DB + API keys
   - `frontend` service: placeholder (Ralph B will fill this in)
   - Shared network

4. Create `backend/Dockerfile`:
   - Python 3.12 slim base
   - Install uv, copy project, `uv sync`, run uvicorn

5. Create `backend/src/agentic_rpg/config.py`:
   - Pydantic Settings: database_url, anthropic_api_key, host, port, log_level, model_name

6. Create `backend/src/agentic_rpg/db.py`:
   - asyncpg pool creation/teardown helpers

7. Create `backend/src/agentic_rpg/main.py`:
   - FastAPI app with lifespan (create/close DB pool)
   - Health endpoint: GET /api/health

8. Implement ALL Pydantic models from specs:

   **models/character.py**: Character, CharacterStats, StatusEffect
   **models/inventory.py**: Item, ItemType (StrEnum), Inventory, Equipment
   **models/world.py**: Location, World
   **models/story.py**: StoryBeat, StoryOutline, StoryState, AdaptationRecord, BeatStatus (StrEnum)
   **models/game_state.py**: GameState, Session, Conversation, Message
   **models/events.py**: GameEvent, EventPayload, all payload models (LocationChangedPayload, StatChangedPayload, ItemAcquiredPayload, etc.)
   **models/api.py**: SessionCreateRequest, SessionCreateResponse, SessionListResponse, SessionSummary, PlayerAction, AgentResponse, StateUpdate, ErrorResponse, HealthResponse

   Follow conventions from `docs/specs/schema-registry.md`:
   - Field descriptions on every field
   - StrEnum for fixed value sets
   - Defaults for optional fields
   - Frozen config for events

9. Create Alembic config:
   - `alembic.ini` pointing at asyncpg URL
   - `alembic/env.py` configured for async
   - Initial migration: `game_sessions` table (id UUID PK, player_id UUID, state JSONB, schema_version INT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ), `game_events` table (event_id UUID PK, event_type TEXT, payload JSONB, source TEXT, session_id UUID FK, timestamp TIMESTAMPTZ)

10. Write tests:
    - `test_models/test_schemas.py`: Instantiate every model, validate serialization round-trip, test validation errors on bad data
    - `test_api/test_health.py`: GET /api/health returns 200
    - Test that Docker Compose builds (manual verification)

### Definition of Done
- `uv run pytest` passes all model tests and health endpoint test
- `docker compose build` succeeds
- `docker compose up` starts postgres + backend, health endpoint responds

---

## Phase 2: State Manager (asyncpg) + Event Bus

### Goal
Implement CRUD for game state via asyncpg and the in-process async event bus with Pydantic validation.

### Specs
- `docs/specs/game-state.md`
- `docs/specs/event-system.md`

### Tests First (RED)

**test_state/test_manager.py**:
- `test_create_session` — creates a new session, returns GameState with valid session_id
- `test_load_session` — loads a previously created session, state matches
- `test_save_session` — modifies state, saves, reloads, changes persisted
- `test_delete_session` — deletes session, load returns None
- `test_load_nonexistent` — returns None or raises SessionNotFound

**test_events/test_bus.py**:
- `test_publish_subscribe` — subscribe to event type, publish event, callback receives it
- `test_multiple_subscribers` — multiple callbacks all fire
- `test_unsubscribe` — unsubscribed callback does not fire
- `test_history` — published events appear in history
- `test_history_filtering` — filter by event_type, session_id
- `test_payload_validation` — publishing with invalid payload raises error

**test_events/test_persistence.py**:
- `test_persist_event` — event written to DB, queryable
- `test_query_by_session` — filter events by session_id
- `test_query_by_type` — filter events by event_type

### Implementation (GREEN)

**state/manager.py**: StateManager class with create, load, save, delete using asyncpg pool
**events/bus.py**: EventBus class with publish, subscribe, unsubscribe, get_history using asyncio.gather
**events/schemas.py**: Event payload registry — register payload models per event type, validate on publish
**events/persistence.py**: persist_event, query_events functions using asyncpg

### Tests need a real Postgres
- Use a test fixture that creates a temporary database or uses a test schema
- conftest.py: fixture that provides an asyncpg pool connected to test DB

### Definition of Done
- All state manager tests pass against real Postgres
- All event bus tests pass
- All event persistence tests pass

---

## Phase 3: Tool Registry + All Tools

### Goal
Implement the LangChain tool registry and every game tool from the spec.

### Specs
- `docs/specs/tool-registry.md`

### Tests First (RED)

**test_tools/test_registry.py**:
- `test_register_tool` — register a tool, retrieve it by name
- `test_duplicate_name_rejected` — registering same name twice raises error
- `test_list_tools` — lists all registered tools
- `test_list_by_category` — filters by category
- `test_get_tools_for_binding` — returns list suitable for llm.bind_tools()

**test_tools/test_character_tools.py**:
- `test_get_character` — returns current character state
- `test_update_health` — modifies health, emits event
- `test_update_health_clamps` — health doesn't go below 0 or above max
- `test_update_energy` — modifies energy, emits event
- `test_add_status_effect` — adds effect to character
- `test_remove_status_effect` — removes effect

**test_tools/test_inventory_tools.py**:
- `test_get_inventory` — returns current inventory
- `test_add_item` — adds item, emits event
- `test_remove_item` — removes item, emits event
- `test_equip_item` — equips to slot, emits event
- `test_use_item` — uses consumable, emits event

**test_tools/test_world_tools.py**:
- `test_get_current_location` — returns location details
- `test_move_character` — moves to connected location, emits event
- `test_move_to_unconnected_fails` — returns error
- `test_add_location` — adds new location to world
- `test_set_world_flag` — sets flag, emits event

**test_tools/test_narrative_tools.py**:
- `test_get_story_outline` — returns current outline
- `test_resolve_beat` — marks beat as resolved, emits event
- `test_advance_beat` — moves to next beat
- `test_adapt_outline` — modifies remaining beats

### Implementation (GREEN)

**tools/registry.py**: ToolRegistry class wrapping a dict of LangChain tools with category metadata
**tools/character.py**: All character tools using BaseTool with injected state
**tools/inventory.py**: All inventory tools
**tools/world.py**: All world tools
**tools/narrative.py**: All narrative tools

Each tool:
1. Validates params (Pydantic args_schema)
2. Checks preconditions
3. Modifies state via state manager
4. Emits events via event bus
5. Returns result dict

### Definition of Done
- All tool tests pass
- Registry tests pass
- Tools correctly emit events when modifying state

---

## Phase 4: Agent Graph + LLM Integration

### Goal
Implement the LangGraph agent state graph that processes player actions through the full loop: context assembly → LLM call → tool execution → response.

### Specs
- `docs/specs/agent-system.md`
- `docs/tech/langchain-integration.md`

### Tests First (RED)

**test_agent/test_graph.py**:
- `test_graph_compiles` — graph builds without error
- `test_simple_action_no_tools` — mock LLM returns text only, graph produces response
- `test_action_with_tool_call` — mock LLM returns tool call, tool executes, LLM called again, response produced
- `test_tool_error_recovery` — mock LLM makes bad tool call, error returned, LLM retries
- `test_recursion_limit` — graph stops after max iterations

**test_agent/test_context.py**:
- `test_context_assembly` — given game state, produces correct message list
- `test_system_prompt_includes_state` — character, location, inventory in system prompt
- `test_system_prompt_includes_story` — story outline in system prompt
- `test_conversation_windowing` — old messages trimmed

**test_agent/test_llm_client.py**:
- `test_create_anthropic_client` — creates ChatAnthropic instance
- `test_bind_tools` — binds tools to model

### Implementation (GREEN)

**llm/client.py**: Factory function to create ChatAnthropic with config
**agent/prompt.py**: Build system prompt from game state using ChatPromptTemplate
**agent/context.py**: Context assembly node — load state, build prompt, trim messages
**agent/graph.py**: LangGraph StateGraph with nodes: context_assembly, call_model, execute_tools (ToolNode), deliver_response. Conditional edges for tool call loop.

Use `FakeListChatModel` or `FakeMessagesListChatModel` from langchain for tests.

### Definition of Done
- All agent tests pass with mocked LLM
- Graph correctly loops through tool calls
- Context assembly produces valid prompts

---

## Phase 5: Story Engine

### Goal
Implement story outline generation and adaptation using LangChain structured output.

### Specs
- `docs/specs/story-engine.md`

### Tests First (RED)

**test_agent/test_story_engine.py**:
- `test_generate_outline` — given setting + character, produces StoryOutline with valid beats
- `test_outline_has_minimum_beats` — at least 5 beats
- `test_beat_lifecycle` — beat transitions: planned → active → resolved
- `test_resolve_beat` — resolving beat updates status and summary
- `test_skip_beat` — skipping beat marks it skipped
- `test_adapt_outline` — adaptation replaces unresolved beats, logs in history
- `test_adaptation_preserves_resolved` — resolved beats are never changed
- `test_summary_updated_on_resolve` — story summary updates after beat resolves

### Implementation (GREEN)

**agent/story_engine.py** (new file):
- `generate_outline(llm, setting, character_summary) -> StoryOutline` — uses `llm.with_structured_output(StoryOutline)`
- `resolve_beat(state, beat_index, outcome) -> StoryState` — marks beat resolved, updates summary
- `skip_beat(state, beat_index) -> StoryState`
- `adapt_outline(llm, state, reason, changes) -> StoryOutline` — regenerates remaining beats
- `advance_beat(state) -> StoryState` — moves active beat forward

Mock LLM in tests to return predefined structured output.

### Definition of Done
- All story engine tests pass
- Outline generation produces valid Pydantic models
- Beat lifecycle works correctly

---

## Phase 6: FastAPI Wiring (HTTP + WebSocket)

### Goal
Wire everything together — HTTP endpoints for session management, WebSocket for gameplay, response streaming.

### Specs
- `docs/specs/api-layer.md`

### Tests First (RED)

**test_api/test_sessions.py**:
- `test_create_session` — POST /api/v1/sessions returns session with game state
- `test_list_sessions` — GET /api/v1/sessions returns list
- `test_get_session` — GET /api/v1/sessions/{id} returns full state
- `test_delete_session` — DELETE /api/v1/sessions/{id} succeeds
- `test_get_nonexistent_session` — returns 404

**test_api/test_game_state.py**:
- `test_get_state_summary` — GET /api/v1/sessions/{id}/state returns summary
- `test_get_inventory` — GET /api/v1/sessions/{id}/inventory returns items
- `test_get_history` — GET /api/v1/sessions/{id}/history returns messages

**test_api/test_websocket.py**:
- `test_websocket_connect` — connects, receives connected message
- `test_player_action` — send action, receive agent response
- `test_state_updates_pushed` — state changes pushed as state_update messages
- `test_invalid_session_rejected` — connection to bad session_id fails

### Implementation (GREEN)

**api/dependencies.py**: Depends providers for db pool, state manager, event bus, agent graph, tool registry
**api/handlers.py**: All HTTP endpoint handlers
**api/websocket.py**: WebSocket endpoint with:
  - Connection management
  - Player action → agent graph invocation
  - Response streaming via astream_events
  - State update forwarding from event bus
**api/routes.py**: Mount all routes on APIRouter
**api/middleware.py**: CORS, error handlers
**main.py**: Wire everything in lifespan, mount routes

### Definition of Done
- All API tests pass
- All WebSocket tests pass
- `docker compose up` starts full stack
- Can create a session and play via WebSocket (manual test)
- Swagger UI at /docs works

---

## Notes for Ralph

- Use `docs/specs/` and `docs/tech/` as authoritative references for implementation details
- Follow the conventions in `docs/specs/schema-registry.md` for all Pydantic models
- Follow the project structure in `docs/tech/python-backend.md`
- Use the LangChain patterns shown in `docs/tech/langchain-integration.md`
- Tests use pytest + pytest-asyncio
- For DB tests, use a real Postgres instance (from docker-compose) with test fixtures that create/drop test data
- Mock LLM calls in tests using langchain's FakeListChatModel or FakeMessagesListChatModel
- Keep it simple — best effort, working > pretty
- Commit after each phase with a descriptive message
