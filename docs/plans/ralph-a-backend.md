# Ralph A — Backend Plan

## Overview

Build the entire Python/FastAPI backend in 6 sequential phases using red/green TDD. Each phase writes failing tests first, then implements the minimum code to pass. Best effort — ugly is fine, working is required.

**Stack**: Python 3.12+, FastAPI, uvicorn, uv, Pydantic v2, asyncpg, Alembic, LangChain, LangGraph, LangSmith, pytest, Docker Compose, PostgreSQL.

**Key constraint**: Every phase must leave `uv run pytest` passing before moving on.

---

## Phase 1: Scaffold + Docker Compose + Postgres + All Pydantic Models

### Goal
Set up the full project structure, Docker Compose environment, database, and every Pydantic model defined across all specs.

### Checklist

#### Project Setup
- [ ] Create `backend/` directory
- [ ] Create `backend/pyproject.toml` with uv (project name: `agentic-rpg`)
- [ ] Add dependencies: fastapi, uvicorn[standard], pydantic, pydantic-settings, asyncpg, alembic, langchain-core, langchain-anthropic, langgraph, structlog
- [ ] Add dev dependencies: pytest, pytest-asyncio, httpx
- [ ] Run `uv sync` — lockfile generated, dependencies install

#### Directory Structure (per `docs/tech/python-backend.md`)
- [ ] `backend/src/agentic_rpg/__init__.py`
- [ ] `backend/src/agentic_rpg/main.py`
- [ ] `backend/src/agentic_rpg/config.py`
- [ ] `backend/src/agentic_rpg/db.py`
- [ ] `backend/src/agentic_rpg/api/__init__.py`
- [ ] `backend/src/agentic_rpg/api/routes.py`
- [ ] `backend/src/agentic_rpg/api/handlers.py`
- [ ] `backend/src/agentic_rpg/api/websocket.py`
- [ ] `backend/src/agentic_rpg/api/middleware.py`
- [ ] `backend/src/agentic_rpg/api/dependencies.py`
- [ ] `backend/src/agentic_rpg/agent/__init__.py`
- [ ] `backend/src/agentic_rpg/agent/graph.py`
- [ ] `backend/src/agentic_rpg/agent/context.py`
- [ ] `backend/src/agentic_rpg/agent/prompt.py`
- [ ] `backend/src/agentic_rpg/tools/__init__.py`
- [ ] `backend/src/agentic_rpg/tools/registry.py`
- [ ] `backend/src/agentic_rpg/tools/character.py`
- [ ] `backend/src/agentic_rpg/tools/inventory.py`
- [ ] `backend/src/agentic_rpg/tools/world.py`
- [ ] `backend/src/agentic_rpg/tools/narrative.py`
- [ ] `backend/src/agentic_rpg/state/__init__.py`
- [ ] `backend/src/agentic_rpg/state/manager.py`
- [ ] `backend/src/agentic_rpg/state/migrations.py`
- [ ] `backend/src/agentic_rpg/events/__init__.py`
- [ ] `backend/src/agentic_rpg/events/bus.py`
- [ ] `backend/src/agentic_rpg/events/schemas.py`
- [ ] `backend/src/agentic_rpg/events/persistence.py`
- [ ] `backend/src/agentic_rpg/models/__init__.py`
- [ ] `backend/src/agentic_rpg/models/game_state.py`
- [ ] `backend/src/agentic_rpg/models/character.py`
- [ ] `backend/src/agentic_rpg/models/inventory.py`
- [ ] `backend/src/agentic_rpg/models/world.py`
- [ ] `backend/src/agentic_rpg/models/story.py`
- [ ] `backend/src/agentic_rpg/models/events.py`
- [ ] `backend/src/agentic_rpg/models/api.py`
- [ ] `backend/src/agentic_rpg/llm/__init__.py`
- [ ] `backend/src/agentic_rpg/llm/client.py`
- [ ] `backend/src/agentic_rpg/llm/types.py`
- [ ] `backend/tests/__init__.py`
- [ ] `backend/tests/conftest.py`
- [ ] `backend/tests/test_models/__init__.py`
- [ ] `backend/tests/test_state/__init__.py`
- [ ] `backend/tests/test_events/__init__.py`
- [ ] `backend/tests/test_tools/__init__.py`
- [ ] `backend/tests/test_agent/__init__.py`
- [ ] `backend/tests/test_api/__init__.py`

#### Docker Compose (`docker-compose.yml` at project root)
- [ ] `postgres` service: postgres:16, port 5432, volume `pgdata`, health check (`pg_isready`), env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- [ ] `backend` service: build from `backend/`, port 8080, depends_on postgres (healthy), env vars for DATABASE_URL, ANTHROPIC_API_KEY
- [ ] `frontend` service: placeholder comment (Ralph B fills in)
- [ ] Shared network: `rpg-network`
- [ ] Named volume: `pgdata`

#### Backend Dockerfile (`backend/Dockerfile`)
- [ ] Python 3.12 slim base
- [ ] Install uv (via pip or copy from official image)
- [ ] Copy pyproject.toml and uv.lock
- [ ] Run `uv sync --frozen`
- [ ] Copy source code
- [ ] CMD: `uv run uvicorn agentic_rpg.main:app --host 0.0.0.0 --port 8080`
- [ ] Expose port 8080

#### Config (`config.py`)
- [ ] Pydantic Settings class with: database_url, anthropic_api_key (default ""), host (default "0.0.0.0"), port (default 8080), log_level (default "info"), model_name (default "claude-sonnet-4-20250514")
- [ ] env_prefix = "" or appropriate prefix

#### Database (`db.py`)
- [ ] `create_pool(database_url) -> asyncpg.Pool` function
- [ ] `close_pool(pool)` function

#### FastAPI App (`main.py`)
- [ ] FastAPI app with lifespan context manager
- [ ] Lifespan: create asyncpg pool on startup, close on shutdown
- [ ] Store pool in app.state.db_pool
- [ ] GET /api/health endpoint returning `{"status": "ok", "version": "0.1.0"}`
- [ ] CORS middleware (allow all origins for dev)

#### Pydantic Models — Character (`models/character.py`)
- [ ] `StatusEffect` model: name (str), duration (int | None), description (str)
- [ ] `Character` model: id (UUID), name (str), profession (str), background (str), stats (dict[str, float]), status_effects (list[StatusEffect]), level (int), experience (int), location_id (str)
- [ ] Field descriptions on every field
- [ ] Defaults for optional fields

#### Pydantic Models — Inventory (`models/inventory.py`)
- [ ] `ItemType` StrEnum: weapon, armor, consumable, key, misc
- [ ] `Item` model: id (UUID), name (str), description (str), item_type (ItemType), quantity (int, ge=1), properties (dict[str, Any])
- [ ] `Inventory` model: items (list[Item]), equipment (dict[str, UUID | None]), capacity (int | None)

#### Pydantic Models — World (`models/world.py`)
- [ ] `Location` model: id (str), name (str), description (str), connections (list[str]), npcs_present (list[str]), items_present (list[str]), visited (bool)
- [ ] `World` model: locations (dict[str, Location]), current_location_id (str), discovered_locations (set[str]), world_flags (dict[str, Any])

#### Pydantic Models — Story (`models/story.py`)
- [ ] `BeatStatus` StrEnum: planned, active, resolved, skipped, adapted
- [ ] `StoryBeat` model: summary (str), location (str), trigger_conditions (list[str]), key_elements (list[str]), player_objectives (list[str]), possible_outcomes (list[str]), flexibility (Literal["fixed", "flexible", "optional"]), status (BeatStatus)
- [ ] `StoryOutline` model: premise (str), setting (str), beats (list[StoryBeat])
- [ ] `AdaptationRecord` model: timestamp (datetime), reason (str), beats_before (list[StoryBeat]), beats_after (list[StoryBeat])
- [ ] `StoryState` model: outline (StoryOutline), active_beat_index (int), summary (str), adaptation_history (list[AdaptationRecord])

#### Pydantic Models — Game State (`models/game_state.py`)
- [ ] `Message` model: role (Literal["player", "agent", "system"]), content (str), timestamp (datetime), metadata (dict[str, Any])
- [ ] `Conversation` model: history (list[Message]), window_size (int), summary (str)
- [ ] `Session` model: session_id (UUID), player_id (UUID), created_at (datetime), updated_at (datetime), schema_version (int), status (Literal["active", "paused", "completed", "abandoned"])
- [ ] `GameState` model: session (Session), character (Character), inventory (Inventory), world (World), story (StoryState), conversation (Conversation), recent_events (list)

#### Pydantic Models — Events (`models/events.py`)
- [ ] `GameEvent` model: event_id (UUID), event_type (str), payload (dict), source (str), session_id (UUID), timestamp (datetime). Frozen config.
- [ ] `EventPayload` base model (frozen)
- [ ] `StatChangedPayload`: stat_name, old_value, new_value, reason
- [ ] `LocationChangedPayload`: old_location_id, new_location_id, location_name
- [ ] `ItemAcquiredPayload`: item_id, item_name, quantity
- [ ] `ItemRemovedPayload`: item_id, item_name, quantity
- [ ] `ItemEquippedPayload`: item_id, slot
- [ ] `StatusEffectAddedPayload`: effect_name, duration
- [ ] `StatusEffectRemovedPayload`: effect_name
- [ ] `BeatResolvedPayload`: beat_index, outcome
- [ ] `BeatActivatedPayload`: beat_index, summary
- [ ] `OutlineAdaptedPayload`: reason
- [ ] `SessionCreatedPayload`: session_id, player_id
- [ ] `WorldFlagChangedPayload`: key, old_value, new_value

#### Pydantic Models — API (`models/api.py`)
- [ ] `CharacterCreate` model: name, profession, background
- [ ] `SessionCreateRequest` model: genre (str), character (CharacterCreate)
- [ ] `SessionCreateResponse` model: session_id (str), game_state (GameState)
- [ ] `SessionSummary` model: session_id, status, character_name, created_at, updated_at
- [ ] `SessionListResponse` model: sessions (list[SessionSummary])
- [ ] `SessionDetailResponse` model: game_state (GameState)
- [ ] `PlayerActionData` model: text (str, min_length=1, max_length=2000)
- [ ] `AgentResponseData` model: text (str), is_complete (bool)
- [ ] `StateUpdateData` model: event_type (str), changes (dict)
- [ ] `ErrorResponseData` model: code (str), message (str)
- [ ] `HealthResponse` model: status (str), version (str)
- [ ] `DeleteResponse` model: success (bool)

#### Alembic Setup
- [ ] `backend/alembic.ini` with asyncpg sqlalchemy URL
- [ ] `backend/alembic/env.py` configured for async migrations
- [ ] `backend/alembic/versions/` directory exists
- [ ] Initial migration: `game_sessions` table (session_id UUID PK, player_id UUID, state JSONB, schema_version INT DEFAULT 1, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now())
- [ ] Initial migration: `game_events` table (event_id UUID PK, event_type TEXT NOT NULL, payload JSONB, source TEXT, session_id UUID REFERENCES game_sessions, timestamp TIMESTAMPTZ DEFAULT now())
- [ ] Index on game_events(session_id)
- [ ] Index on game_events(event_type)

#### Tests — Phase 1
- [ ] `tests/test_models/test_schemas.py`: test_character_model — create Character, validate fields
- [ ] `tests/test_models/test_schemas.py`: test_inventory_model — create Inventory with items
- [ ] `tests/test_models/test_schemas.py`: test_world_model — create World with locations
- [ ] `tests/test_models/test_schemas.py`: test_story_model — create StoryState with outline and beats
- [ ] `tests/test_models/test_schemas.py`: test_game_state_model — create full GameState, validate nesting
- [ ] `tests/test_models/test_schemas.py`: test_game_state_serialization_roundtrip — model_dump_json → model_validate_json
- [ ] `tests/test_models/test_schemas.py`: test_event_model_frozen — GameEvent cannot be mutated
- [ ] `tests/test_models/test_schemas.py`: test_item_type_enum — ItemType values are valid strings
- [ ] `tests/test_models/test_schemas.py`: test_validation_errors — invalid data raises ValidationError
- [ ] `tests/test_api/test_health.py`: test_health_endpoint — GET /api/health returns 200 with status "ok"
- [ ] All tests pass: `uv run pytest`

#### Build Verification
- [ ] `docker compose build` succeeds
- [ ] `docker compose up -d postgres` starts postgres, health check passes
- [ ] `docker compose up -d backend` starts backend, health endpoint responds on localhost:8080/api/health
- [ ] Commit Phase 1: `git add -A && git commit -m "phase 1: scaffold, docker, models"`

---

## Phase 2: State Manager (asyncpg) + Event Bus

### Goal
Implement CRUD for game state via asyncpg and the in-process async event bus with Pydantic validation.

### Specs to reference
- `docs/specs/game-state.md`
- `docs/specs/event-system.md`

### Checklist

#### Test Fixtures
- [ ] `tests/conftest.py`: fixture `db_pool` — creates asyncpg pool to test Postgres (use docker-compose postgres or env var)
- [ ] `tests/conftest.py`: fixture `clean_db` — truncates game_sessions and game_events tables before each test
- [ ] `tests/conftest.py`: fixture `sample_game_state` — returns a valid GameState instance for testing
- [ ] `tests/conftest.py`: fixture `event_bus` — returns a fresh EventBus instance

#### Tests — State Manager (RED first, then GREEN)
- [ ] `tests/test_state/test_manager.py`: `test_create_session` — creates new session, returns GameState with valid session_id
- [ ] `tests/test_state/test_manager.py`: `test_load_session` — loads previously created session, state matches what was created
- [ ] `tests/test_state/test_manager.py`: `test_save_session` — modify character name, save, reload, name changed
- [ ] `tests/test_state/test_manager.py`: `test_delete_session` — delete session, load returns None
- [ ] `tests/test_state/test_manager.py`: `test_load_nonexistent` — loading random UUID returns None
- [ ] `tests/test_state/test_manager.py`: `test_list_sessions` — create 3 sessions, list returns all 3
- [ ] `tests/test_state/test_manager.py`: `test_list_sessions_by_player` — list filtered by player_id

#### Implementation — State Manager
- [ ] `state/manager.py`: `StateManager.__init__(self, pool: asyncpg.Pool)`
- [ ] `state/manager.py`: `async create_session(self, player_id, genre, character_create) -> GameState` — builds initial GameState, inserts into DB
- [ ] `state/manager.py`: `async load_session(self, session_id) -> GameState | None` — SELECT state FROM game_sessions, deserialize
- [ ] `state/manager.py`: `async save_session(self, state: GameState) -> None` — UPDATE state, updated_at
- [ ] `state/manager.py`: `async delete_session(self, session_id) -> bool` — DELETE, return whether row existed
- [ ] `state/manager.py`: `async list_sessions(self, player_id=None) -> list[SessionSummary]` — SELECT with optional filter
- [ ] All state manager tests pass

#### Tests — Event Bus (RED first, then GREEN)
- [ ] `tests/test_events/test_bus.py`: `test_publish_subscribe` — subscribe callback, publish event, callback called with event
- [ ] `tests/test_events/test_bus.py`: `test_multiple_subscribers` — 2 callbacks both receive the event
- [ ] `tests/test_events/test_bus.py`: `test_unsubscribe` — unsubscribed callback not called on next publish
- [ ] `tests/test_events/test_bus.py`: `test_subscriber_error_doesnt_block_others` — one bad callback doesn't prevent others
- [ ] `tests/test_events/test_bus.py`: `test_history` — published events appear in get_history()
- [ ] `tests/test_events/test_bus.py`: `test_history_filter_by_type` — filter history by event_type
- [ ] `tests/test_events/test_bus.py`: `test_history_filter_by_session` — filter history by session_id
- [ ] `tests/test_events/test_bus.py`: `test_history_bounded` — history doesn't grow past max size
- [ ] `tests/test_events/test_bus.py`: `test_payload_validation` — registering payload model, publishing invalid payload raises error

#### Implementation — Event Bus
- [ ] `events/bus.py`: `EventBus.__init__(self, max_history=1000)`
- [ ] `events/bus.py`: `async publish(self, event: GameEvent) -> None` — validate payload, notify subscribers, add to history
- [ ] `events/bus.py`: `subscribe(self, event_type: str, callback) -> str` — returns subscription_id
- [ ] `events/bus.py`: `unsubscribe(self, subscription_id: str) -> None`
- [ ] `events/bus.py`: `async get_history(self, event_type=None, session_id=None, limit=100) -> list[GameEvent]`
- [ ] `events/schemas.py`: `EventPayloadRegistry` — register(event_type, PydanticModel), validate(event_type, payload)
- [ ] All event bus tests pass

#### Tests — Event Persistence (RED first, then GREEN)
- [ ] `tests/test_events/test_persistence.py`: `test_persist_event` — persist event, query it back
- [ ] `tests/test_events/test_persistence.py`: `test_query_by_session` — persist 3 events across 2 sessions, filter works
- [ ] `tests/test_events/test_persistence.py`: `test_query_by_type` — persist mixed event types, filter by type works
- [ ] `tests/test_events/test_persistence.py`: `test_query_pagination` — limit and offset work

#### Implementation — Event Persistence
- [ ] `events/persistence.py`: `async persist_event(pool, event: GameEvent) -> None` — INSERT into game_events
- [ ] `events/persistence.py`: `async query_events(pool, session_id=None, event_type=None, limit=100, offset=0) -> list[GameEvent]`
- [ ] All event persistence tests pass

#### Phase 2 Wrap-up
- [ ] All Phase 2 tests pass: `uv run pytest tests/test_state/ tests/test_events/`
- [ ] All Phase 1 tests still pass: `uv run pytest`
- [ ] Commit Phase 2: `git add -A && git commit -m "phase 2: state manager + event bus"`

---

## Phase 3: Tool Registry + All Tools

### Goal
Implement the LangChain tool registry and every game tool from the spec.

### Specs to reference
- `docs/specs/tool-registry.md`

### Checklist

#### Test Fixtures
- [ ] `tests/conftest.py`: fixture `tool_game_state` — returns a GameState with character at a location, items in inventory, story with beats
- [ ] `tests/conftest.py`: fixture `tool_event_bus` — returns an EventBus with payload schemas registered
- [ ] `tests/conftest.py`: fixture `tool_registry` — returns a populated ToolRegistry with all tools registered

#### Tests — Registry (RED first, then GREEN)
- [ ] `tests/test_tools/test_registry.py`: `test_register_tool` — register a tool, get_tool returns it
- [ ] `tests/test_tools/test_registry.py`: `test_duplicate_name_rejected` — registering same name raises ValueError
- [ ] `tests/test_tools/test_registry.py`: `test_list_tools` — returns all registered tool names + descriptions
- [ ] `tests/test_tools/test_registry.py`: `test_list_by_category` — filters by category string
- [ ] `tests/test_tools/test_registry.py`: `test_get_tools_for_binding` — returns list of LangChain tool objects

#### Implementation — Registry
- [ ] `tools/registry.py`: `ToolRegistry` class with _tools dict and _categories dict
- [ ] `tools/registry.py`: `register(self, tool, category: str)` — stores tool by name, records category
- [ ] `tools/registry.py`: `get_tool(self, name) -> BaseTool`
- [ ] `tools/registry.py`: `list_tools(self) -> list[dict]` — name + description pairs
- [ ] `tools/registry.py`: `list_by_category(self, category) -> list[BaseTool]`
- [ ] `tools/registry.py`: `get_tools_for_binding(self) -> list[BaseTool]`
- [ ] All registry tests pass

#### Tests — Character Tools (RED first, then GREEN)
- [ ] `tests/test_tools/test_character_tools.py`: `test_get_character` — returns character dict
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_health_positive` — adds health, emits stat_changed event
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_health_negative` — reduces health, emits event
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_health_clamp_floor` — health doesn't go below 0
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_health_clamp_ceiling` — health doesn't exceed max_health
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_energy` — modifies energy, emits event
- [ ] `tests/test_tools/test_character_tools.py`: `test_add_status_effect` — adds to status_effects list
- [ ] `tests/test_tools/test_character_tools.py`: `test_remove_status_effect` — removes from list
- [ ] `tests/test_tools/test_character_tools.py`: `test_remove_nonexistent_effect` — returns error, no crash
- [ ] `tests/test_tools/test_character_tools.py`: `test_update_money` — modifies money stat

#### Implementation — Character Tools
- [ ] `tools/character.py`: Pydantic input models (UpdateHealthInput, UpdateEnergyInput, AddStatusEffectInput, RemoveStatusEffectInput, UpdateMoneyInput)
- [ ] `tools/character.py`: `get_character` tool — returns character state as dict
- [ ] `tools/character.py`: `update_health` tool — clamp to 0..max, emit stat_changed
- [ ] `tools/character.py`: `update_energy` tool — clamp to 0..max, emit stat_changed
- [ ] `tools/character.py`: `add_status_effect` tool — append to list, emit event
- [ ] `tools/character.py`: `remove_status_effect` tool — remove from list, emit event
- [ ] `tools/character.py`: `update_money` tool — modify money stat, emit event
- [ ] All character tool tests pass

#### Tests — Inventory Tools (RED first, then GREEN)
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_get_inventory` — returns inventory dict
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_add_item` — item appears in inventory, event emitted
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_add_duplicate_stacks` — adding same item increases quantity
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_remove_item` — item removed, event emitted
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_remove_partial_quantity` — reduces quantity, doesn't remove
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_remove_nonexistent_item` — returns error
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_equip_item` — item moved to equipment slot, event emitted
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_equip_nonexistent_item` — returns error
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_use_consumable` — quantity decremented, event emitted
- [ ] `tests/test_tools/test_inventory_tools.py`: `test_use_non_consumable` — returns error

#### Implementation — Inventory Tools
- [ ] `tools/inventory.py`: Pydantic input models (AddItemInput, RemoveItemInput, EquipItemInput, UnequipItemInput, UseItemInput)
- [ ] `tools/inventory.py`: `get_inventory` tool
- [ ] `tools/inventory.py`: `add_item` tool — add or stack
- [ ] `tools/inventory.py`: `remove_item` tool — remove or decrement
- [ ] `tools/inventory.py`: `equip_item` tool — validate item exists, move to slot
- [ ] `tools/inventory.py`: `unequip_item` tool
- [ ] `tools/inventory.py`: `use_item` tool — validate consumable, decrement
- [ ] All inventory tool tests pass

#### Tests — World Tools (RED first, then GREEN)
- [ ] `tests/test_tools/test_world_tools.py`: `test_get_current_location` — returns location dict
- [ ] `tests/test_tools/test_world_tools.py`: `test_get_connections` — returns list of connected location names/ids
- [ ] `tests/test_tools/test_world_tools.py`: `test_move_character_valid` — moves to connected location, emits event
- [ ] `tests/test_tools/test_world_tools.py`: `test_move_character_invalid` — unconnected location returns error
- [ ] `tests/test_tools/test_world_tools.py`: `test_move_updates_visited` — destination marked as visited
- [ ] `tests/test_tools/test_world_tools.py`: `test_add_location` — new location added to world
- [ ] `tests/test_tools/test_world_tools.py`: `test_add_location_with_connections` — connections wired both ways
- [ ] `tests/test_tools/test_world_tools.py`: `test_set_world_flag` — flag set in world_flags, event emitted
- [ ] `tests/test_tools/test_world_tools.py`: `test_set_world_flag_overwrite` — overwrites existing flag

#### Implementation — World Tools
- [ ] `tools/world.py`: Pydantic input models (MoveCharacterInput, AddLocationInput, SetWorldFlagInput)
- [ ] `tools/world.py`: `get_current_location` tool
- [ ] `tools/world.py`: `get_connections` tool
- [ ] `tools/world.py`: `move_character` tool — validate connection, update location_id, emit event
- [ ] `tools/world.py`: `add_location` tool — add to world.locations
- [ ] `tools/world.py`: `set_world_flag` tool — set flag, emit event
- [ ] All world tool tests pass

#### Tests — Narrative Tools (RED first, then GREEN)
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_get_story_outline` — returns outline dict
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_resolve_beat` — marks current beat as resolved, emits event
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_resolve_beat_wrong_index` — resolving non-active beat returns error
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_advance_beat` — active_beat_index increments
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_advance_past_end` — returns error or wraps
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_adapt_outline` — replaces future beats
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_add_beat` — inserts beat at position
- [ ] `tests/test_tools/test_narrative_tools.py`: `test_update_story_summary` — updates summary string

#### Implementation — Narrative Tools
- [ ] `tools/narrative.py`: Pydantic input models (ResolveBeatInput, AdaptOutlineInput, AddBeatInput, UpdateStorySummaryInput)
- [ ] `tools/narrative.py`: `get_story_outline` tool
- [ ] `tools/narrative.py`: `resolve_beat` tool — validate active beat, mark resolved, emit event
- [ ] `tools/narrative.py`: `advance_beat` tool — increment index, activate next beat
- [ ] `tools/narrative.py`: `adapt_outline` tool — replace unresolved beats
- [ ] `tools/narrative.py`: `add_beat` tool — insert at position
- [ ] `tools/narrative.py`: `update_story_summary` tool
- [ ] All narrative tool tests pass

#### Phase 3 Wrap-up
- [ ] All Phase 3 tests pass: `uv run pytest tests/test_tools/`
- [ ] All previous tests still pass: `uv run pytest`
- [ ] Commit Phase 3: `git add -A && git commit -m "phase 3: tool registry + all tools"`

---

## Phase 4: Agent Graph + LLM Integration

### Goal
Implement the LangGraph agent state graph that processes player actions.

### Specs to reference
- `docs/specs/agent-system.md`
- `docs/tech/langchain-integration.md`

### Checklist

#### Test Fixtures
- [ ] `tests/conftest.py`: fixture `mock_llm` — returns a FakeListChatModel or FakeMessagesListChatModel
- [ ] `tests/conftest.py`: fixture `mock_llm_with_tools` — returns mock LLM that returns tool call messages
- [ ] `tests/conftest.py`: fixture `agent_graph` — returns compiled agent graph with mock LLM

#### Tests — LLM Client (RED first, then GREEN)
- [ ] `tests/test_agent/test_llm_client.py`: `test_create_anthropic_client` — creates ChatAnthropic instance with config
- [ ] `tests/test_agent/test_llm_client.py`: `test_create_client_with_custom_model` — respects model_name setting
- [ ] `tests/test_agent/test_llm_client.py`: `test_bind_tools` — client.bind_tools(tools) returns bound model

#### Implementation — LLM Client
- [ ] `llm/client.py`: `create_llm(settings) -> ChatAnthropic` — creates ChatAnthropic with api_key, model, temperature
- [ ] `llm/client.py`: `bind_tools_to_llm(llm, tools) -> ChatAnthropic` — calls llm.bind_tools(tools)
- [ ] All LLM client tests pass

#### Tests — Context Assembly (RED first, then GREEN)
- [ ] `tests/test_agent/test_context.py`: `test_build_system_prompt` — given GameState, produces string with character/location/inventory
- [ ] `tests/test_agent/test_context.py`: `test_system_prompt_includes_story` — story outline premise and active beat in prompt
- [ ] `tests/test_agent/test_context.py`: `test_system_prompt_includes_recent_events` — recent events formatted in prompt
- [ ] `tests/test_agent/test_context.py`: `test_context_assembly_node` — given AgentState, returns updated state with messages
- [ ] `tests/test_agent/test_context.py`: `test_conversation_windowing` — messages beyond window_size are trimmed

#### Implementation — Context Assembly
- [ ] `agent/prompt.py`: `build_system_prompt(game_state: GameState) -> str` — formats game state into system prompt string using ChatPromptTemplate
- [ ] `agent/context.py`: `context_assembly_node(state: AgentState) -> dict` — loads state, builds prompt, trims messages
- [ ] All context tests pass

#### Tests — Agent Graph (RED first, then GREEN)
- [ ] `tests/test_agent/test_graph.py`: `test_graph_compiles` — build_agent_graph returns CompiledGraph
- [ ] `tests/test_agent/test_graph.py`: `test_simple_action_no_tools` — mock LLM returns text, graph produces response with content
- [ ] `tests/test_agent/test_graph.py`: `test_action_with_single_tool_call` — mock LLM calls get_character, then responds with text
- [ ] `tests/test_agent/test_graph.py`: `test_action_with_multiple_tool_calls` — mock LLM calls 2 tools, then responds
- [ ] `tests/test_agent/test_graph.py`: `test_tool_error_recovery` — mock LLM makes bad tool call, gets error, retries successfully
- [ ] `tests/test_agent/test_graph.py`: `test_graph_state_includes_events` — events emitted during tool execution are in final state
- [ ] `tests/test_agent/test_graph.py`: `test_recursion_limit` — graph stops after configurable max iterations

#### Implementation — Agent Graph
- [ ] `agent/graph.py`: `AgentState` TypedDict (messages, session_id, game_state, events)
- [ ] `agent/graph.py`: `context_assembly_node` — delegates to context.py
- [ ] `agent/graph.py`: `call_model_node` — calls LLM with messages
- [ ] `agent/graph.py`: `deliver_response_node` — extracts final text response
- [ ] `agent/graph.py`: `should_execute_tools(state) -> str` — checks for tool_calls, returns "tools" or "respond"
- [ ] `agent/graph.py`: `build_agent_graph(tools, chat_model, state_manager, event_bus) -> CompiledGraph`
- [ ] Graph wiring: entry → context_assembly → call_model → conditional(tools/respond) → execute_tools → call_model (loop) / deliver_response → END
- [ ] All agent graph tests pass

#### Phase 4 Wrap-up
- [ ] All Phase 4 tests pass: `uv run pytest tests/test_agent/`
- [ ] All previous tests still pass: `uv run pytest`
- [ ] Commit Phase 4: `git add -A && git commit -m "phase 4: agent graph + LLM integration"`

---

## Phase 5: Story Engine

### Goal
Implement story outline generation and adaptation using LangChain structured output.

### Specs to reference
- `docs/specs/story-engine.md`

### Checklist

#### Tests — Story Engine (RED first, then GREEN)
- [ ] `tests/test_agent/test_story_engine.py`: `test_generate_outline` — mock LLM, returns StoryOutline with valid beats
- [ ] `tests/test_agent/test_story_engine.py`: `test_outline_has_minimum_beats` — generated outline has >= 5 beats
- [ ] `tests/test_agent/test_story_engine.py`: `test_outline_beats_start_as_planned` — all beats have status "planned"
- [ ] `tests/test_agent/test_story_engine.py`: `test_first_beat_activated` — after generation, first beat status is "active"
- [ ] `tests/test_agent/test_story_engine.py`: `test_resolve_beat` — resolving active beat sets status to "resolved", records outcome
- [ ] `tests/test_agent/test_story_engine.py`: `test_resolve_beat_updates_summary` — story summary is updated after resolve
- [ ] `tests/test_agent/test_story_engine.py`: `test_skip_beat` — skip sets status to "skipped"
- [ ] `tests/test_agent/test_story_engine.py`: `test_advance_beat` — active_beat_index increments, next beat becomes "active"
- [ ] `tests/test_agent/test_story_engine.py`: `test_adapt_outline` — mock LLM, unresolved beats replaced, adaptation logged
- [ ] `tests/test_agent/test_story_engine.py`: `test_adaptation_preserves_resolved_beats` — resolved beats unchanged after adaptation
- [ ] `tests/test_agent/test_story_engine.py`: `test_adaptation_history_recorded` — AdaptationRecord added to history
- [ ] `tests/test_agent/test_story_engine.py`: `test_generate_initial_story_state` — creates full StoryState from outline

#### Implementation — Story Engine
- [ ] `agent/story_engine.py`: `async generate_outline(llm, setting: str, character_summary: str) -> StoryOutline`
  - Uses `llm.with_structured_output(StoryOutline)`
  - Prompt template asks for 5-10 beats with narrative arc
- [ ] `agent/story_engine.py`: `activate_first_beat(outline: StoryOutline) -> StoryOutline` — sets first beat to "active"
- [ ] `agent/story_engine.py`: `create_initial_story_state(outline: StoryOutline) -> StoryState`
- [ ] `agent/story_engine.py`: `resolve_beat(story_state: StoryState, outcome: str) -> StoryState`
- [ ] `agent/story_engine.py`: `skip_beat(story_state: StoryState) -> StoryState`
- [ ] `agent/story_engine.py`: `advance_beat(story_state: StoryState) -> StoryState`
- [ ] `agent/story_engine.py`: `async adapt_outline(llm, story_state: StoryState, reason: str, changes: str) -> StoryState`
  - Uses structured output to regenerate remaining beats
  - Preserves resolved beats
  - Logs AdaptationRecord
- [ ] All story engine tests pass

#### Phase 5 Wrap-up
- [ ] All Phase 5 tests pass: `uv run pytest tests/test_agent/test_story_engine.py`
- [ ] All previous tests still pass: `uv run pytest`
- [ ] Commit Phase 5: `git add -A && git commit -m "phase 5: story engine"`

---

## Phase 6: FastAPI Wiring (HTTP + WebSocket)

### Goal
Wire everything together into a running API server.

### Specs to reference
- `docs/specs/api-layer.md`

### Checklist

#### Test Fixtures
- [ ] `tests/conftest.py`: fixture `app_client` — async httpx client against the FastAPI app with test DB
- [ ] `tests/conftest.py`: fixture `ws_client` — WebSocket test client
- [ ] `tests/conftest.py`: fixture `seeded_session` — creates a session in DB, returns session_id

#### Tests — Session Endpoints (RED first, then GREEN)
- [ ] `tests/test_api/test_sessions.py`: `test_create_session` — POST /api/v1/sessions with genre + character, returns 200 with session_id and game_state
- [ ] `tests/test_api/test_sessions.py`: `test_create_session_validation` — missing fields returns 422
- [ ] `tests/test_api/test_sessions.py`: `test_list_sessions` — GET /api/v1/sessions returns list
- [ ] `tests/test_api/test_sessions.py`: `test_list_sessions_empty` — returns empty list when no sessions
- [ ] `tests/test_api/test_sessions.py`: `test_get_session` — GET /api/v1/sessions/{id} returns full state
- [ ] `tests/test_api/test_sessions.py`: `test_get_nonexistent_session` — returns 404
- [ ] `tests/test_api/test_sessions.py`: `test_delete_session` — DELETE /api/v1/sessions/{id} returns success
- [ ] `tests/test_api/test_sessions.py`: `test_delete_nonexistent_session` — returns 404

#### Tests — Game State Endpoints (RED first, then GREEN)
- [ ] `tests/test_api/test_game_state.py`: `test_get_state_summary` — GET /api/v1/sessions/{id}/state returns character + location + beat summary
- [ ] `tests/test_api/test_game_state.py`: `test_get_inventory` — GET /api/v1/sessions/{id}/inventory returns items and equipment
- [ ] `tests/test_api/test_game_state.py`: `test_get_history` — GET /api/v1/sessions/{id}/history returns messages with pagination

#### Tests — WebSocket (RED first, then GREEN)
- [ ] `tests/test_api/test_websocket.py`: `test_websocket_connect` — connect to /api/v1/sessions/{id}/ws, receive "connected" message with game state
- [ ] `tests/test_api/test_websocket.py`: `test_websocket_invalid_session` — connect to bad session_id, connection closed with error
- [ ] `tests/test_api/test_websocket.py`: `test_player_action` — send player_action, receive agent_response messages (mocked LLM)
- [ ] `tests/test_api/test_websocket.py`: `test_player_action_streaming` — receive multiple chunks before is_complete=true
- [ ] `tests/test_api/test_websocket.py`: `test_state_updates_pushed` — when agent calls a tool, state_update message received

#### Implementation — Dependencies
- [ ] `api/dependencies.py`: `get_db_pool(request) -> asyncpg.Pool`
- [ ] `api/dependencies.py`: `get_state_manager(pool) -> StateManager`
- [ ] `api/dependencies.py`: `get_event_bus(request) -> EventBus`
- [ ] `api/dependencies.py`: `get_tool_registry(state, event_bus) -> ToolRegistry`
- [ ] `api/dependencies.py`: `get_agent_graph(registry, llm) -> CompiledGraph`

#### Implementation — HTTP Handlers
- [ ] `api/handlers.py`: `create_session` — POST /api/v1/sessions
- [ ] `api/handlers.py`: `list_sessions` — GET /api/v1/sessions
- [ ] `api/handlers.py`: `get_session` — GET /api/v1/sessions/{session_id}
- [ ] `api/handlers.py`: `delete_session` — DELETE /api/v1/sessions/{session_id}
- [ ] `api/handlers.py`: `get_state_summary` — GET /api/v1/sessions/{session_id}/state
- [ ] `api/handlers.py`: `get_inventory` — GET /api/v1/sessions/{session_id}/inventory
- [ ] `api/handlers.py`: `get_history` — GET /api/v1/sessions/{session_id}/history

#### Implementation — WebSocket
- [ ] `api/websocket.py`: WebSocket endpoint at /api/v1/sessions/{session_id}/ws
- [ ] `api/websocket.py`: On connect: validate session, accept, send "connected" with game state
- [ ] `api/websocket.py`: On receive player_action: invoke agent graph, stream response chunks
- [ ] `api/websocket.py`: Forward state_update events from event bus to WebSocket
- [ ] `api/websocket.py`: Handle disconnect gracefully

#### Implementation — Wiring
- [ ] `api/routes.py`: Mount all HTTP routes on APIRouter with /api/v1 prefix
- [ ] `api/routes.py`: Mount WebSocket route
- [ ] `api/middleware.py`: CORS middleware (allow all for dev)
- [ ] `api/middleware.py`: GameError exception handler
- [ ] `main.py`: Wire lifespan — create DB pool, run Alembic migrations, create EventBus, store in app.state
- [ ] `main.py`: Mount routes from api/routes.py
- [ ] `main.py`: Include health endpoint

#### Phase 6 Wrap-up
- [ ] All Phase 6 tests pass: `uv run pytest tests/test_api/`
- [ ] All tests pass: `uv run pytest`
- [ ] `docker compose up` starts full stack (postgres + backend)
- [ ] Health endpoint responds: `curl localhost:8080/api/health`
- [ ] Swagger UI works: open `localhost:8080/docs` in browser
- [ ] Can create session via curl: `curl -X POST localhost:8080/api/v1/sessions -H "Content-Type: application/json" -d '{"genre":"fantasy","character":{"name":"Aldric","profession":"knight","background":"A wandering knight"}}'`
- [ ] Commit Phase 6: `git add -A && git commit -m "phase 6: FastAPI wiring + WebSocket"`

---

## Notes for Ralph

- Use `docs/specs/` and `docs/tech/` as authoritative references for implementation details
- Follow the conventions in `docs/specs/schema-registry.md` for all Pydantic models
- Follow the project structure in `docs/tech/python-backend.md`
- Use the LangChain patterns shown in `docs/tech/langchain-integration.md`
- Tests use pytest + pytest-asyncio
- For DB tests, use the docker-compose postgres with test fixtures that create/drop test data
- Mock LLM calls in tests using langchain's FakeListChatModel or FakeMessagesListChatModel
- Keep it simple — best effort, working > pretty
- Commit after each phase with a descriptive message
- Check off items in this checklist as you complete them (edit this file)
- If a test is failing and you can't fix it quickly, skip it with `@pytest.mark.skip` and move on — velocity matters
