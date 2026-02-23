# Roadmap

This is the ordered build plan. Each phase produces a working increment. Implementation plans for each phase are generated separately in `docs/plans/` as work begins.

---

## Phase 1: Project Scaffolding & Schema Foundation

**Goal**: Set up the new Go + Next.js project structure, Docker Compose environment, database, and the JSON Schema registry with codegen pipeline.

**Systems involved**:
- [Schema Registry](specs/schema-registry.md) + [Schema Codegen](tech/schema-codegen.md)
- [PostgreSQL](tech/postgres.md)
- [Docker & Kubernetes](tech/docker-kubernetes.md)
- [Go Backend](tech/go-backend.md) (project skeleton)
- [Next.js Frontend](tech/nextjs-frontend.md) (project skeleton)

**Deliverables**:
- `docker-compose.yml` with Go server, Postgres, and Next.js frontend
- Go project skeleton (`cmd/server/main.go`, basic HTTP server, health endpoint)
- Next.js project skeleton (home page, basic layout)
- `schemas/` directory with initial schemas (character, game state, session)
- Codegen script that generates Go structs and TypeScript types
- Postgres migrations for players, sessions, events tables
- CI can build and test both projects

**Why first**: Everything else depends on the project structure, database, and shared schemas.

---

## Phase 2: Game State & Session Management

**Goal**: Implement the state management layer — creating sessions, persisting game state to Postgres, loading it back.

**Systems involved**:
- [Game State](specs/game-state.md)
- [API Layer](specs/api-layer.md) (session endpoints only)

**Deliverables**:
- State manager (create, load, save, delete sessions)
- HTTP endpoints: POST /sessions, GET /sessions, GET /sessions/:id, DELETE /sessions/:id
- Game state stored as JSONB in Postgres
- Schema versioning support
- Unit tests for state manager
- Integration tests for session endpoints

**Why second**: The agent needs state to work with. State management is the foundation for everything interactive.

---

## Phase 3: Event System

**Goal**: Implement the event bus with JSON Schema validation and event persistence.

**Systems involved**:
- [Event System](specs/event-system.md)

**Deliverables**:
- In-process event bus (publish, subscribe, history)
- Event schema registry (register schemas, validate payloads)
- Event persistence to Postgres events table
- Event query API (by session, type, time range)
- Unit tests for bus, schema validation, persistence

**Why third**: Tools emit events. The agent context includes events. This needs to exist before tools and the agent are built.

---

## Phase 4: Tool Registry & Core Tools

**Goal**: Implement the tool registry and the initial set of game tools (character, inventory, world, narrative).

**Systems involved**:
- [Tool Registry](specs/tool-registry.md)
- [Event System](specs/event-system.md) (tools emit events)
- [Game State](specs/game-state.md) (tools modify state)

**Deliverables**:
- Tool registry (register, discover, execute pipeline)
- Character tools (get_character, update_health, update_energy, add/remove status effects)
- Inventory tools (get_inventory, add_item, remove_item, equip, use)
- World tools (get_current_location, move_character, add_location, set_world_flag)
- Narrative tools (get_story_outline, resolve_beat, adapt_outline, advance_beat)
- Tools emit events on state changes
- Unit tests for every tool
- Integration tests for tool → state → event flow

**Why fourth**: The agent calls tools. Tools need state management and the event system. This is the last dependency before the agent.

---

## Phase 5: Agent System & LLM Integration

**Goal**: Implement the agent loop — context assembly, LLM API calls with tool use, response streaming.

**Systems involved**:
- [Agent System](specs/agent-system.md)
- [LLM Integration](tech/llm-integration.md)
- [Tool Registry](specs/tool-registry.md)

**Deliverables**:
- LLM API client (Anthropic Claude, with provider interface for future OpenAI support)
- Agent loop (receive input → assemble context → call LLM → execute tools → return response)
- Context assembly (system prompt + state + events + conversation + tools)
- Response streaming support
- Context window management (conversation windowing, history summarization)
- Retry and error handling for LLM calls
- Unit tests with mocked LLM client
- Integration test: player action → agent → tool calls → state changes → response

**Why fifth**: This is the core intelligence. It depends on everything built so far.

---

## Phase 6: Story Engine

**Goal**: Implement story outline generation and adaptation.

**Systems involved**:
- [Story Engine](specs/story-engine.md)
- [Agent System](specs/agent-system.md) (agent uses narrative tools)

**Deliverables**:
- Story outline generation (LLM call with structured output)
- Story beat lifecycle (planned → active → resolved/skipped/adapted)
- Outline adaptation (detect divergence → regenerate remaining beats)
- Story summary maintenance
- Integration with agent context (outline in context, narrative tools available)
- Integration with session creation (generate outline on new game)
- Tests for outline generation, beat lifecycle, adaptation

**Why sixth**: The story engine builds on top of a working agent. It's the feature that makes the game feel coherent rather than random.

---

## Phase 7: WebSocket & Real-Time Frontend

**Goal**: Implement WebSocket communication and build the gameplay frontend.

**Systems involved**:
- [WebSockets](tech/websockets.md)
- [API Layer](specs/api-layer.md) (WebSocket protocol)
- [Frontend](specs/frontend.md)

**Deliverables**:
- WebSocket hub (connection management, session routing)
- WebSocket protocol (player_action, agent_response, state_update, heartbeat)
- Response streaming over WebSocket (LLM tokens → WS chunks)
- Event bus → WebSocket bridge (state changes pushed to client)
- Frontend: home screen (session list, new game)
- Frontend: character creation flow
- Frontend: game screen (narrative panel, character panel, inventory, location)
- Frontend: WebSocket connection manager (connect, reconnect, dispatch)
- Frontend: Zustand store synced with server state
- End-to-end test: create game → play → see streaming responses → see state updates

**Why seventh**: This is the user-facing layer. It needs all backend systems working first.

---

## Phase 8: Polish & Deployment

**Goal**: Harden the system, add observability, prepare for deployment.

**Systems involved**:
- [Docker & Kubernetes](tech/docker-kubernetes.md)
- All systems (hardening)

**Deliverables**:
- Structured logging throughout the backend
- Error handling audit (no unhandled errors, graceful degradation)
- Token usage tracking and budget enforcement
- Graceful shutdown (drain WebSockets, finish in-flight requests)
- Dockerfile optimization (small images, multi-stage builds)
- Kubernetes manifests (Deployment, Service, Ingress, Secrets)
- Helm chart (optional)
- Deploy to a K8s cluster (minikube or cloud)
- Load testing with multiple concurrent sessions

**Why last**: Polish and deployment require a working system. Don't optimize what doesn't exist yet.

---

## Future Phases (Not Scheduled)

These are captured in the individual spec "Future Extensions" sections:

- **Multi-agent system**: Specialized agents for combat, NPC dialogue, world events
- **Combat system**: Turn-based or real-time combat with its own agent and tools
- **NPC system**: NPCs with personalities, memories, and relationship tracking
- **Weather / dynamic world events**: Background systems that evolve the world
- **Player accounts and auth**: OAuth, persistent accounts across sessions
- **Mobile support**: Responsive frontend for phones/tablets
- **Analytics**: Gameplay data collection and dashboard
