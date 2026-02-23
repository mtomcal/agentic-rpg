# Event System Specification

## Overview

The event system provides loose coupling between components. When something happens in the game (a character moves, an item is picked up, a story beat resolves), an event is emitted. Other components can subscribe to events they care about. All events are schema-validated against a JSON schema registry.

## Core Concepts

### Events

An event is an immutable record of something that happened. Every event has:

- **Type**: A dotted string identifier (e.g., `character.moved`, `inventory.item_acquired`, `story.beat_resolved`)
- **Payload**: A data object whose shape is defined by the event's schema
- **Source**: Which component or tool emitted the event
- **Session ID**: Which game session this event belongs to
- **Timestamp**: When the event occurred
- **Event ID**: Unique identifier for this specific event instance

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

This is not exhaustive. New event types can be added as systems are built. The schema registry is the authoritative list.

### Event Schema Registry

Every event type has a registered JSON Schema that defines the shape of its payload. The registry provides:

- **Registration**: Add a new event type with its payload schema
- **Validation**: Validate an event's payload against its registered schema before emission
- **Discovery**: List all registered event types and their schemas
- **Documentation**: Each schema includes descriptions for all fields

If an event is emitted with no registered schema, it should be rejected. This ensures all events are well-defined.

### Event Bus

The event bus is the in-process pub/sub mechanism:

- **Publish**: Emit a validated event to all subscribers of that event type
- **Subscribe**: Register a callback for a specific event type
- **Unsubscribe**: Remove a subscription
- **History**: The bus keeps a bounded in-memory history of recent events (configurable size, default 1000)
- **Replay**: Retrieve events from history, filtered by type, session, or time range

The bus is synchronous within a single action — when an event is published, all subscribers are called before returning. Subscriber errors are logged but do not block other subscribers or the publisher.

### Event Persistence

Events are also written to the database for long-term storage and debugging. The in-memory history is a cache for fast access during the agent loop. The database is the durable record.

Persisted events support:
- Query by session ID
- Query by event type
- Query by time range
- Pagination for large result sets

## Integration Points

### Tools → Event Bus

Tools emit events after modifying state. For example, the `move_character` tool:
1. Updates the character's location in game state
2. Emits `world.location_changed` with the old and new location
3. Returns success to the agent

### Event Bus → Agent Context

The agent's context assembly pulls recent events from the bus to include in the LLM context. This lets the agent "remember" what just happened without re-reading the full state.

### Event Bus → WebSocket

A subscriber on the event bus forwards relevant events to the player's WebSocket connection. This drives real-time UI updates.

### Event Bus → Logging/Observability

A subscriber logs all events for debugging and monitoring.

## Design Constraints

- Events are immutable once emitted
- Event ordering is guaranteed within a session (events are sequential because actions are sequential)
- The bus is in-process only — no cross-process or cross-server messaging (for now)
- Subscribers must not emit events that trigger themselves (no infinite loops)

## Future Extensions

- **Cross-service event bus**: For multi-service deployment, use a message broker (NATS, Redis Streams)
- **Event sourcing**: Reconstruct game state entirely from the event log
- **Event-driven NPCs**: NPCs subscribe to events and react autonomously
- **Analytics**: Aggregate events for gameplay analytics and balancing
