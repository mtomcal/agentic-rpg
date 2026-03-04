# Event System Specification

## Overview

The event system provides loose coupling between components. When something happens in the game (a character moves, an item is picked up, a story beat resolves), an event is emitted. Other components can subscribe to events they care about. All event payloads are validated using Pydantic v2 models.

## Core Concepts

### Events

An event is an immutable record of something that happened. Every event is represented as a Pydantic model with the following fields:

- **Type**: A dotted string identifier (e.g., `character.moved`, `inventory.item_acquired`, `story.beat_resolved`)
- **Payload**: A Pydantic model instance whose schema is determined by the event type
- **Source**: Which component or tool emitted the event
- **Session ID**: Which game session this event belongs to
- **Timestamp**: When the event occurred (`datetime`)
- **Event ID**: Unique identifier for this specific event instance (`uuid4`)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class GameEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    payload: dict  # validated against the registered Pydantic model for this type
    source: str
    session_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}  # events are immutable
```

Events are facts, not commands. They describe what *happened*, not what *should* happen. Components react to events, but events themselves are passive.

### Event Types

Event types are organized by domain:

**Character events:**
- `character.created` — A new character was created
- `character.stat_changed` — A stat was modified (health, energy, etc.)
- `character.status_effect_added` — A status effect was applied
- `character.status_effect_removed` — A status effect expired or was removed
- `character.leveled_up` — Character gained a level
- `character.died` — Character health reached zero

**Inventory events:**
- `inventory.item_acquired` — An item was added to inventory
- `inventory.item_removed` — An item was removed from inventory
- `inventory.item_equipped` — An item was equipped
- `inventory.item_unequipped` — An item was unequipped
- `inventory.item_used` — A consumable was used

**World events:**
- `world.location_changed` — Player moved to a new location
- `world.location_discovered` — A new location was revealed
- `world.flag_changed` — A world state flag was set or changed
- `world.npc_spawned` — An NPC appeared at a location
- `world.npc_removed` — An NPC left a location

**Story events:**
- `story.outline_generated` — A new story outline was created
- `story.beat_activated` — A story beat became active
- `story.beat_resolved` — A story beat was completed
- `story.beat_skipped` — A story beat was bypassed
- `story.outline_adapted` — The story outline was modified
- `story.summary_updated` — The running story summary was updated

**Session events:**
- `session.created` — A new game session started
- `session.saved` — Game state was persisted
- `session.loaded` — Game state was loaded
- `session.ended` — Game session ended

**Agent events:**
- `agent.action_started` — Agent began processing a player action
- `agent.action_completed` — Agent finished processing
- `agent.tool_called` — Agent invoked a tool
- `agent.error` — Agent encountered an error

This is not exhaustive. New event types can be added as systems are built. The Pydantic model registry is the authoritative list.

### Event Payload Models

Every event type has a registered Pydantic model that defines the shape of its payload. Each payload model extends a common `EventPayload` base:

```python
class EventPayload(BaseModel):
    """Base class for all event payloads."""
    model_config = {"frozen": True}

class LocationChangedPayload(EventPayload):
    old_location_id: str
    new_location_id: str
    location_name: str

class StatChangedPayload(EventPayload):
    stat_name: str
    old_value: float
    new_value: float
    reason: str = ""
```

The payload registry provides:

- **Registration**: Register a Pydantic model for an event type via a decorator or explicit call
- **Validation**: Validate an event's payload against the registered model before emission (Pydantic validates automatically on instantiation)
- **Discovery**: List all registered event types and their payload models
- **Documentation**: Pydantic models generate JSON Schema automatically, providing self-documenting event contracts

If an event is emitted with no registered payload model, it should be rejected. This ensures all events are well-defined.

> **Implementation note:** The `EventPayloadRegistry.validate_payload()` method exists but is not currently called by `EventBus.publish()`. Payload validation is therefore not enforced at publish time.

### Event Bus

The event bus is an in-process async pub/sub mechanism built on Python's `asyncio`:

```python
class EventBus:
    async def publish(self, event: GameEvent) -> None: ...
    def publish_sync(self, event: GameEvent) -> None: ...
    def subscribe(self, event_type: str, callback: Callable[[GameEvent], Awaitable[None]]) -> str: ...
    def unsubscribe(self, subscription_id: str) -> None: ...
    async def get_history(self, event_type: str | None = None, session_id: UUID | None = None, limit: int = 100) -> list[GameEvent]: ...
```

- **Publish**: Emit a validated event to all subscribers of that event type. Subscribers are invoked concurrently using `asyncio.gather`.
- **Publish (sync)**: A synchronous variant of publish for use in non-async contexts. Schedules subscriber invocations without awaiting them.
- **Subscribe**: Register an async callback for a specific event type. Returns a subscription ID.
- **Unsubscribe**: Remove a subscription by ID.
- **History**: The bus keeps a bounded in-memory history of recent events (configurable size, default 1000) using a `collections.deque`.
- **Replay**: Retrieve events from history, filtered by type, session, or time range.

When an event is published, all subscribers are awaited concurrently via `asyncio.gather(*tasks, return_exceptions=True)`. Subscriber errors are logged but do not block other subscribers or the publisher.

Alternatively, the [blinker](https://blinker.readthedocs.io/) library can provide the pub/sub backbone, with async dispatch wrappers.

### LangChain Callback Integration

Agent events bridge into the event bus through LangChain callback handlers. A custom `GameEventCallbackHandler` extends `BaseCallbackHandler` and translates LangChain lifecycle events into game events:

```python
from langchain_core.callbacks import BaseCallbackHandler

class GameEventCallbackHandler(BaseCallbackHandler):
    def __init__(self, event_bus: EventBus, session_id: UUID):
        self.event_bus = event_bus
        self.session_id = session_id

    def on_tool_start(self, serialized, input_str, **kwargs):
        # Emit agent.tool_called event
        ...

    def on_llm_start(self, serialized, prompts, **kwargs):
        # Emit agent.action_started event
        ...

    def on_llm_end(self, response, **kwargs):
        # Emit agent.action_completed event
        ...

    def on_llm_error(self, error, **kwargs):
        # Emit agent.error event
        ...
```

This allows all LangChain/LangGraph agent activity to flow through the same event system as game state changes.

### Event Persistence

Events are also written to PostgreSQL via `asyncpg` for long-term storage and debugging. The in-memory history is a cache for fast access during the agent loop. The database is the durable record.

```python
async def persist_event(pool: asyncpg.Pool, event: GameEvent) -> None:
    await pool.execute(
        """INSERT INTO game_events (event_id, event_type, payload, source, session_id, timestamp)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        event.event_id, event.event_type,
        event.payload,  # stored as JSONB
        event.source, event.session_id, event.timestamp,
    )
```

Persisted events support:
- Query by session ID
- Query by event type
- Query by time range
- Pagination for large result sets

Database schema is managed by Alembic migrations.

## Integration Points

### Tools → Event Bus

Tools emit events after modifying state. For example, the `move_character` tool:
1. Updates the character's location in game state
2. Emits `world.location_changed` with the old and new location
3. Returns success to the agent

### Event Bus → Agent Context

The agent's context assembly pulls recent events from the bus to include in the LLM context. This lets the agent "remember" what just happened without re-reading the full state.

### Event Bus → WebSocket

A subscriber on the event bus forwards relevant events to the player's WebSocket connection (via FastAPI WebSocket endpoints). This drives real-time UI updates.

### Event Bus → Logging/Observability

A subscriber logs all events for debugging and monitoring. Events are also visible in LangSmith traces when emitted during agent processing.

## Design Constraints

- Events are immutable once emitted (enforced by Pydantic's `frozen` model config)
- Event ordering is guaranteed within a session (events are sequential because actions are sequential)
- The bus is in-process only — no cross-process or cross-server messaging (for now)
- Subscribers must not emit events that trigger themselves (no infinite loops)
- All event bus methods are async-compatible for use within the asyncio event loop

## Future Extensions

- **Cross-service event bus**: For multi-service deployment, use a message broker (NATS, Redis Streams)
- **Event sourcing**: Reconstruct game state entirely from the event log
- **Event-driven NPCs**: NPCs subscribe to events and react autonomously
- **Analytics**: Aggregate events for gameplay analytics and balancing
