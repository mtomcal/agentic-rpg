# AGENTS.md — Agentic RPG

<!-- TREE-HASH: a3f0d817e89c7fbaa274d74ff35b9bb9587267f866f5100a794fc92db0d6a868 -->

## Map

<!-- TREE-START -->
```
.
├── backend
│   ├── alembic
│   │   └── versions
│   ├── scripts
│   ├── src
│   │   └── agentic_rpg
│   │       ├── agent
│   │       ├── api
│   │       ├── events
│   │       ├── llm
│   │       ├── models
│   │       ├── state
│   │       └── tools
│   └── tests
│       ├── test_agent
│       ├── test_api
│       ├── test_events
│       ├── test_llm
│       ├── test_models
│       ├── test_state
│       └── test_tools
├── docs
│   ├── plans
│   ├── specs
│   └── tech
├── explainer
└── frontend
    ├── app
    │   ├── new
    │   └── play
    │       └── [sessionId]
    ├── components
    ├── lib
    ├── __tests__
    │   ├── app
    │   ├── components
    │   ├── integration
    │   ├── lib
    │   └── types
    └── types
```
<!-- TREE-END -->

---

## Modules

### `backend/src/agentic_rpg/api/` — API Layer

- **Purpose**: FastAPI route registration (REST + WebSocket), request handlers, dependency injection, structured error handling (GameError), CORS middleware. Owns the HTTP boundary and negotiates external ↔ internal data.
- **Owns**: `routes.py`, `handlers.py`, `websocket.py`, `dependencies.py`, `middleware.py`
- **Depends on**: `state` (StateManager for read-only lookups + writes), `events` (EventBus, EventPersistence), `models` (API schemas), `agent` (graph execution)
- **Rules**: Never imports from `tools/` directly — all tool interaction flows through the agent graph. Read-only calls to `state/` are fine (GET endpoints). Writes go through `agent/` → `tools/` → `state/` to ensure events are emitted.
- **Entry points**: `routes.register_routes()` called by `main.py`. WebSocket endpoint at `/ws/{session_id}`.

### `backend/src/agentic_rpg/agent/` — Agent Graph

- **Purpose**: LangGraph state graph that orchestrates the LLM agent loop — routes between LLM calls, tool execution (`ToolNode`), and response delivery. Call model → conditional edge to tools or respond → terminal. Context assembly, prompt construction, story engine.
- **Owns**: `graph.py`, `context.py`, `prompt.py`, `story_engine.py`
- **Depends on**: `models` (GameState, AgentState), `tools` (tool list for LLM binding), `events` (EventBus for context enrichment), `llm` (chat model via `create_chat_model()`)
- **Rules**: The graph is the sole orchestrator — it decides when tools run. `recursion_limit` (default 25) prevents runaway loops. `should_execute_tools` routes on `AIMessage.tool_calls`.
- **Entry points**: `graph.build_agent_graph()` — returns compiled LangGraph `StateGraph` with `ainvoke()`.

### `backend/src/agentic_rpg/tools/` — Game Tools

- **Purpose**: 24 LangChain tools across 4 categories — character (6), inventory (6), world (6), narrative (6). `ToolRegistry` manages lifecycle: registration (with dedup check), discovery by name/category, LLM binding. Every tool receives `game_state` + `event_bus` and **must emit a `GameEvent`** for every state mutation.
- **Owns**: `registry.py`, `character.py`, `inventory.py`, `world.py`, `narrative.py`
- **Depends on**: `models` (GameState for reads/writes), `events` (EventBus.publish_sync for event emission)
- **Rules**: Every state mutation MUST emit a corresponding GameEvent. Tools use `publish_sync()` because they run in LangChain's sync context. Never call `state/` directly — mutation is done by modifying the `game_state` object passed in.
- **Entry points**: `registry.build_all_tools()` — called by agent graph setup.

### `backend/src/agentic_rpg/state/` — State Manager

- **Purpose**: Game state persistence via asyncpg. CRUD on game sessions — create (with player upsert), load, save (JSONB update), delete, list by player, status updates. Single source of truth is the `game_state` JSONB column in the `sessions` table.
- **Owns**: `manager.py`
- **Depends on**: `models` (GameState, SessionStatus), `db.py` (asyncpg pool), PostgreSQL
- **Rules**: Read-only operations are safe to call from `api/` directly. Writes always come through the agent graph → tools → state pipeline. Hardcodes `"fantasy"` as genre in `create_session()` — the API-accepted `genre` param is not persisted.
- **Entry points**: `StateManager` class, injected via FastAPI dependency.

### `backend/src/agentic_rpg/events/` — Event System

- **Purpose**: In-process async pub/sub event bus (`EventBus`) with bounded in-memory history (max 1000 events) + PostgreSQL event persistence (`EventPersistence`). `EventPayloadRegistry` maps event type strings to Pydantic payload models for validation. Typed payloads: StatChangedPayload, LocationChangedPayload, ItemAcquiredPayload, ItemRemovedPayload, BeatResolvedPayload.
- **Owns**: `bus.py`, `persistence.py`, `schemas.py`
- **Depends on**: `models` (GameEvent, typed payloads), `db.py` (asyncpg pool)
- **Rules**: `EventBus.publish()` is async and runs subscribers concurrently — errors are logged not propagated. `publish_sync()` is a fragile workaround for sync tool contexts (drives coroutines via `.send(None)`). Always emit at least the standard event types; the frontend relies on `updateFromStateEvent` in the Zustand store to apply changes from events.
- **Entry points**: `EventBus` (publish/subscribe), `EventPersistence` (save/query), `EventPayloadRegistry` (validate payloads).

### `backend/src/agentic_rpg/models/` — Pydantic Models

- **Purpose**: All Pydantic v2 models — GameState (top-level root), Character, Inventory, World, StoryState, Conversation, Session, API request/response schemas, GameEvent, typed event payloads. GameEvent and EventPayload are `frozen=True`; game domain models are mutable by default. StrEnum for fixed value sets. Field descriptions on every field.
- **Owns**: `game_state.py`, `character.py`, `inventory.py`, `world.py`, `story.py`, `api.py`, `events.py`
- **Depends on**: None (standalone — no cross-module imports. Models import from each other within `models/` only.)
- **Rules**: No business logic in models — pure data containers. No imports from `state/`, `events/`, `tools/`, `agent/`, or `api/`. Type hints everywhere.
- **Entry points**: Re-exported via `models/__init__.py`, consumed by all other modules.

### `backend/src/agentic_rpg/llm/` — LLM Client

- **Purpose**: LLM client factory — creates `ChatAnthropic` or `ChatOpenAI` from `LLMConfig` with validation (provider, model_name, temperature, max_tokens, max_retries, request_timeout). Supports retries and timeout configuration.
- **Owns**: `client.py`, `types.py`
- **Depends on**: `config.py` (Settings)
- **Rules**: Never imports from `models/` — uses its own `LLMConfig` pydantic model. Single point of contact for LLM provider configuration. Tests use mocked/fake chat models.
- **Entry points**: `create_chat_model()` — consumed by agent graph.

### `backend/src/agentic_rpg/main.py` — App Entry Point

- **Purpose**: FastAPI app factory with `lifespan` context manager (creates DB pool, EventBus, EventPersistence, closes on shutdown). Registers routes, CORS middleware (allow all origins), error handlers. Exposes `/health` endpoint.
- **Depends on**: `api/` (routes), `events/` (bus, persistence), `db.py` (pool), `config.py`
- **Rules**: Lifespan is the only place where top-level initialization happens. Do not create DB pools or event busses elsewhere.

### `backend/src/agentic_rpg/db.py` — Database Pool

- **Purpose**: asyncpg connection pool creation and teardown. Used by StateManager and EventPersistence.
- **Depends on**: `config.py` (Settings.DATABASE_URL)
- **Rules**: Pool is created once in `main.py` lifespan and shared via `app.state`. Never create pools in individual modules.

### `backend/src/agentic_rpg/config.py` — Settings

- **Purpose**: Pydantic-settings based configuration — DATABASE_URL, ANTHROPIC_API_KEY, model_name, log level.
- **Depends on**: None

### `backend/tests/` — Backend Test Suite

- **Purpose**: pytest test suite mirroring `src/agentic_rpg/` structure. Shared fixtures in `conftest.py` (DB pool, sample data, mock LLM, event bus). 85%+ coverage required on ALL metrics (lines, branches, functions).
- **Owns**: `test_models/`, `test_state/` (needs Postgres), `test_events/` (bus + schemas unit, persistence DB), `test_agent/` (mock LLM), `test_tools/`, `test_llm/`, `test_api/` (health + WS unit, sessions + game_state DB)
- **Depends on**: All backend modules, PostgreSQL (for DB-dependent tests)
- **Rules**: Tests import from `src/agentic_rpg/` directly. Test categories split by DB dependency: unit tests (no DB) and DB tests (needs Postgres). Tests are the spec — red/green TDD means tests are written before implementation.

### `backend/alembic/` — Database Migrations

- **Purpose**: Alembic-managed PostgreSQL schema migrations. Defines `sessions` (id, player_id, status, genre, schema_version, game_state JSONB, created_at, updated_at), `events` (id, session_id, type, payload JSONB, source, created_at), `players` tables.
- **Depends on**: PostgreSQL (runs at app startup or via `alembic upgrade head`)

### `frontend/app/` — Next.js Pages

- **Purpose**: Next.js 14+ App Router pages — home (`/`), new session (`/new`), play (`/play/[sessionId]`). Layout with global state.
- **Owns**: `page.tsx` (home), `new/page.tsx`, `play/[sessionId]/page.tsx`, `layout.tsx`
- **Depends on**: `lib/` (API client, WebSocket, store), `components/`
- **Entry points**: Next.js App Router route definitions

### `frontend/components/` — React Components

- **Purpose**: 6 display/interaction components — CharacterPanel, ChatPanel, InventoryPanel, LocationPanel, Sidebar, StoryPanel. ChatPanel handles user input + message display. Other panels are read-only displays of game state.
- **Depends on**: `lib/store.ts` (Zustand), `types/game.ts`
- **Rules**: No direct component-to-component imports. All data flows through the shared Zustand store (`lib/store.ts`). Components communicate by reading shared state and dispatching store actions. No direct API calls — data comes from the store which is populated by WebSocket events and initial API fetch.

### `frontend/lib/` — Core Client Logic

- **Purpose**: REST API client (`api.ts`) with player-ID header, WebSocket client (`websocket.ts`) with automatic reconnection, Zustand game store (`store.ts` — GameState + chat messages + connection state), player ID management (`player.ts` — localStorage-based UUID), WebSocket message schema validation (`ws-schemas.ts` with Zod).
- **Owns**: `api.ts`, `websocket.ts`, `store.ts`, `player.ts`, `ws-schemas.ts`
- **Depends on**: `types/` (api.ts, game.ts), `zod` (ws-schemas)
- **Entry points**: `useGameStore` (consumed by all components), `createSession`/`listSessions`/`getSession`/`deleteSession` (API), `connectWebSocket`/`disconnectWebSocket` (WS)

### `frontend/types/` — TypeScript Definitions

- **Purpose**: TypeScript interfaces matching backend Pydantic models + generated OpenAPI types from `openapi-typescript` (`types/generated.ts`)
- **Owns**: `api.ts`, `game.ts`, `generated.ts`
- **Depends on**: None
- **Rules**: No business logic — pure type definitions only. Consumed by `lib/` and `components/`. Never imports from `lib/`.

### `docs/` — Documentation

- **Purpose**: PRD (`docs/prd.md`), roadmap (`docs/roadmap.md`), system specs (8 files in `docs/specs/` — agent, story, state, events, tools, api, frontend, schema), technology decisions (7 files in `docs/tech/`), implementation plans (`docs/plans/` per Ralph).
- **Owns**: `specs/`, `tech/`, `plans/`
- **Depends on**: None

### `explainer/` — Interactive Explainers

- **Purpose**: Generated HTML explainers from the create-explainer skill. Build artifacts, not source code. Each explainer is a self-contained HTML file with embedded JS+CSS.
- **Depends on**: None (generated output)

---

## Dependency Rules

### Backend

- **`api/` must NOT import from `tools/` directly**: All tool interaction flows through `agent/` (the graph). The graph owns tool orchestration. Violation: bypassing the LangGraph routing logic and calling tool internals from handlers.
- **`api/` may import from `state/` for read-only operations**: GET endpoints (load game state, list sessions, health) can call StateManager directly. Writes (save, update status) flow through `agent/` → `tools/` → `state/` to maintain event consistency.
- **`agent/` may import from `tools/`, `llm/`, `models/`, `events/`**: The graph is the integration point. It binds tools to the LLM, builds context from events, and uses models for state shaping.
- **`tools/` must NOT import from `state/`**: Tools mutate the `game_state` object passed in by reference. They do not persist — that's the StateManager's job. Tools do import from `events/` (to emit events via `publish_sync()`).
- **`events/` and `state/` are sibling modules**: Both depend on `db.py` (asyncpg pool) but not on each other. EventPersistence saves GameEvents to the `events` table; StateManager saves GameState to the `sessions` table.
- **`models/` is the leaf dependency**: All modules import from `models/`, but models never import anything outside the `models/` package. This is the innermost layer.
- **`llm/` imports from `config.py` only**: Does not import from `models/`. Uses its own `LLMConfig` Pydantic model.

### Frontend

- **Components must NOT import other components directly**: No `import CharacterPanel from '../CharacterPanel'` inside InventoryPanel. All cross-component communication goes through the Zustand store (`lib/store.ts`).
- **Components must NOT call the API directly**: All API calls go through `lib/api.ts`. Components consume data from the Zustand store, which is populated via initial API fetch and WebSocket event streams.
- **`lib/` imports from `types/`, not the reverse**: Types are pure interfaces with no logic. Never import from `lib/` or `components/` inside `types/`.
- **`types/generated.ts` is auto-generated**: Do not edit manually. Regenerate with `make generate-types` or `npm run generate:types`.

### Cross-Cutting

- **Tests import from source directly**: Backend tests import from `src/agentic_rpg/`. Frontend tests import from `@/components/`, `@/lib/`, etc. Tests are not black-box — they validate internal module behavior.
- **DB-dependent tests are separate from unit tests**: `make test-unit` runs tests that don't need Postgres. `make test-db` starts Postgres, runs DB tests, stops Postgres. Never mix DB and non-DB tests in the same file.

---

## Anti-patterns

- **Pattern: Mutating game state in tools without emitting an event**
  - **Why wrong**: The frontend's `updateFromStateEvent()` relies on event streams to reflect state changes. Missing events mean the UI stays stale. Event history is used for debugging, context assembly, and rollback scenarios.
  - **Right way**: Every tool that modifies a field on `game_state` must also call `event_bus.publish_sync()` with a `GameEvent` before returning. Use the typed payloads from `events/schemas.py` (StatChangedPayload, LocationChangedPayload, etc.).

- **Pattern: Using `EventBus.publish_sync()` in contexts that could be async**
  - **Why wrong**: `publish_sync()` drives coroutines via `.send(None)` which is fragile — it works for simple callbacks but breaks with actual async IO, context switches, or nested awaits. Errors can be silently swallowed.
  - **Right way**: Keep `publish_sync()` only for the LangChain tool context where the runtime is synchronous. For all other contexts (WebSocket message handlers, API endpoints), use `await event_bus.publish()`.

- **Pattern: Hardcoding genre in `StateManager.create_session()`**
  - **Why wrong**: The API accepts a `genre` parameter from the client (`SessionCreateRequest.genre`), but `StateManager.create_session()` hardcodes `"fantasy"` in the SQL INSERT. The genre sent by the client is never persisted.
  - **Right way**: Pass the genre through the GameState model and persist `session.genre` from the state object, not a hardcoded string.

- **Pattern: Vague test assertions (`assert result`, `toBeTruthy()`, `toBeDefined()`)**
  - **Why wrong**: These pass for any non-null, truthy value — they don't verify the actual shape or content of the result. A test that passes with a hardcoded stub is worthless.
  - **Right way**: Assert specific values: `assert result.name == "Aldric"`, `expect(result.stats.health).toBe(80)`. See CLAUDE.md "What Makes a Good Test" for approved patterns.

- **Pattern: Importing across component boundaries directly (frontend)**
  - **Why wrong**: Creates tight coupling between panels. Changing one component's internal structure can break an unrelated component. Makes refactoring harder and violates the single-responsibility of each panel.
  - **Right way**: All cross-component data flows through the Zustand store. Components read from `useGameStore()` and dispatch state changes via store actions.

- **Pattern: Bypassing the agent graph to call tools from API handlers**
  - **Why wrong**: The LangGraph is designed as the single orchestrator — it manages the LLM conversation loop, tool routing, and response delivery. Calling tools directly from handlers bypasses conversation management, event sequencing, and the opportunity for the LLM to reason about tool results.
  - **Right way**: All interactive player actions go through the WebSocket → agent graph → tools pipeline. REST endpoints are for session management (CRUD) only.

---

## Coding Principles

### Test Methodology

- **Strict red/green TDD**: Write a failing test first (RED), then write the minimum implementation to make it pass (GREEN). No refactor phase — speed over elegance; refactor later if needed. Tests are the spec.
- **Coverage: 85% minimum on ALL metrics**: Lines, branches, functions (backend and frontend). Statements also 85% for frontend. This is enforced by `pyproject.toml` (`fail_under = 85`) and `jest.config.js` (`coverageThreshold`).
- **What to test**: Every public function/method, every tool (state changes + event emissions), every API endpoint (success, validation errors, not found, errors), WebSocket (connect, message, stream, disconnect), agent graph (mock LLM, test tool call loops, error recovery), Pydantic models (serialization round-trips, validation errors), frontend components (render with props, user interaction, state updates), frontend lib (API calls, WS messages, store actions).
- **What NOT to test**: `__init__.py` files, imports/re-exports, framework boilerplate, type definitions, generated code.
- **Test doubles**: Mocked/fake LLM for agent tests, in-memory EventBus for tool tests (no real events), test asyncpg pool (via `pgtest` or Docker Postgres) for DB tests.
- **Test categories**: Unit tests (no DB, fast) vs DB tests (needs Postgres, slower). Separate directories and Makefile targets.
- **Tests mirror source structure**: `tests/test_tools/` mirrors `src/agentic_rpg/tools/`. `__tests__/lib/` mirrors `lib/`.

### Design Principles

- **Single Responsibility**: Each module owns one concern (API routes, state persistence, tool registry, event bus, etc.). Tools are single-purpose (one tool = one mutation). Components are single-display.
- **Registry pattern for tools**: `ToolRegistry` provides registration, discovery by name/category, and LLM-ready binding. Prevents duplicate registration. Enables category-based tool selection.
- **Pub/Sub for events**: `EventBus` decouples event emitters (tools) from event consumers (WebSocket broadcast, persistence, frontend state sync).
- **StateGraph for agent orchestration**: LangGraph's `StateGraph` provides explicit node structure (call_model, execute_tools, deliver_response) with conditional edges (`should_execute_tools`). `recursion_limit` prevents infinite loops.
- **Composition over inheritance**: Tools are composed with shared `game_state` + `event_bus` kwargs rather than inheriting from a base tool class.
- **Frozen events, mutable state**: `GameEvent` models are immutable (`frozen=True`) to guarantee event integrity. Game domain models (Character, Inventory, World) are mutable because tools modify them in-place during a turn.

### Code Organization

- **Package-by-feature**: Both backend modules and frontend directories are organized by feature/concern, not by layer. Each module owns its full vertical slice (models, logic, persistence).
- **Single-export module boundaries**: Each backend module's `__init__.py` re-exports the public API. Internal details stay in individual files.
- **Tests mirror source**: Backend `tests/` directory structure mirrors `src/agentic_rpg/`. Frontend `__tests__/` mirrors `frontend/`.
- **No shared utility modules**: Avoid generic `utils.py` or `helpers.py` — code belongs in the feature module that owns it.

### Error Handling

- **Structured errors at API boundary**: `GameError` exception with `code` (machine-readable), `message` (human-readable), and `status_code`. Handled by `register_error_handlers()` in middleware. All API errors return `{"error": {"code": ..., "message": ...}}`.
- **Fail-fast for state operations**: `StateManager.save_game_state()` raises `ValueError` if session not found. `StateManager.update_session_status()` raises on not found. These propagate up to the FastAPI error handlers.
- **Graceful degradation for event subscribers**: `EventBus.publish()` runs all subscriber coroutines with `asyncio.gather(return_exceptions=True)` — subscriber errors are logged but don't block other subscribers or the publisher.
- **LLM client retries**: `LLMConfig.max_retries` (default 3) and `request_timeout` (default 60s) configured via the chat model, retried automatically by LangChain/LangChain Anthropic/OpenAI.
- **No silent error swallowing**: All caught exceptions are logged (not pass/ignore). Use `logger.warning()` at minimum for recovered errors.

### Mutation Rules

- **Game state is the single source of truth**: The full `GameState` is serialized as JSONB in the `sessions` table. Tools receive the object by reference, mutate fields, then the graph saves via StateManager.
- **Mutable game domain objects**: Character, Inventory, World, StoryState, Conversation are mutable — tools modify fields directly on the passed-in `game_state` object. This is intentional for performance (no copy-on-write overhead per turn).
- **Every mutation must emit an event**: For every field change in a tool, a `GameEvent` with a typed payload must be published via `event_bus.publish_sync()`. This is the contract that keeps the frontend state in sync.
- **Side effects at edges only**: Direct state mutations happen in tools. Event publishing happens in tools. Database writes happen in StateManager (called by the graph after tool execution). API handlers do not mutate state directly.

### Naming Conventions

- **Python**: PEP 8. `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants. Type hints on all public functions.
- **TypeScript**: PascalCase for types/interfaces/enums, camelCase for variables/functions, kebab-case for files. `Strict` mode enabled.
- **Event types**: Dotted string format — `character.stat_changed`, `world.location_changed`, `inventory.item_acquired`, `inventory.item_removed`, `story.beat_resolved`.
- **Tool names**: VerbNoun pattern — `UpdateHealthTool`, `MoveCharacterTool`, `AddItemTool`, `AdvanceBeatTool`.
- **API routes**: RESTful plural nouns — `POST /api/v1/sessions`, `GET /api/v1/sessions/{id}`, `DELETE /api/v1/sessions/{id}`.
- **Ubiquitous language**: Domain terms from `docs/specs/` used consistently — "session", "beat", "stat", "event_type", "payload", "status_effect". Avoid generic terms like "thing" or "data" when a domain term exists.

### Review Gates

- **Code review required**: Changes are reviewed before merge. Each Ralph works on its own branch, merges to `main` when done.
- **CI gates**: `make test` (unit + frontend) or `make test-all` (full suite including DB tests) must pass. Coverage must meet 85% threshold on all metrics.
- **Linting**: `ruff check src/` for Python (lint), `ruff format src/` for Python (format), `npm run build` for frontend (type check + build). Enforced via `make lint`.
- **Subagent-based test quality verification**: `test-quality-verifier` subagent audits tests 3 times per phase — after writing tests (assertion quality), after implementation (coverage gaps), before committing (test strength — "would this catch a real bug?").
- **Commit messages**: Descriptive — `"phase N: brief description"`. No vague messages like "fix stuff" or "update".
- **PR checklist implicit** (from CLAUDE.md): Tests written first (RED), implementation passes tests (GREEN), coverage meets threshold, linting passes, commit message descriptive.

---

## Appendix

### Quality Invariants

| Invariant | Enforcement | Tool |
|-----------|-------------|------|
| Coverage ≥ 85% all metrics | `pyproject.toml` fail_under=85, `jest.config.js` coverageThreshold | pytest-cov, jest --coverage |
| Python lint | `ruff check src/` | ruff |
| Python format | `ruff format src/ --check` | ruff |
| TypeScript build | `next build` | Next.js |
| Test-first | Human process (red/green TDD) | — |
| Test quality | Subagent audit (3 passes) | test-quality-verifier |
| DB schema | `alembic upgrade head` | Alembic |

### Ubiquitous Language

See `docs/specs/` for full documentation. Key terms:

| Term | Definition |
|------|-----------|
| **Session** | A game play-through tied to one player and one character |
| **Beat** | A granular story chunk (~1-5 narrative turns) |
| **Stat** | A numeric character attribute (health, energy, money) |
| **Status Effect** | A temporary buff/debuff/condition on a character |
| **Tool** | A LangChain tool that the agent can call to mutate game state |
| **Event** | An immutable record of a state change, with typed payload |
| **GameState** | The complete session state (character, inventory, world, story, conversation) |
| **Graph** | The LangGraph StateGraph that orchestrates the agent loop |
