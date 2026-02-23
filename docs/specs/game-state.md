# Game State Specification

## Overview

The game state is the single source of truth for everything about a player's game. It captures the character, the world, the story, inventory, conversation history, and all other mutable data. The state is persisted to a database and loaded into memory for the duration of a player action.

## State Structure

The game state is a hierarchical document with the following top-level sections:

### Session

- **Session ID**: Unique identifier for this game session
- **Player ID**: The player who owns this session
- **Created at**: When the session was created
- **Updated at**: When the state was last modified
- **Schema version**: Version of the state schema (for migrations)
- **Status**: active, paused, completed, abandoned

### Character

- **ID**: Unique character identifier
- **Name**: Player-chosen name
- **Profession/Class**: Character archetype
- **Background**: Brief character backstory (player-provided or generated)
- **Stats**: Health, max health, energy, max energy, money, and any genre-specific stats
- **Status effects**: Active buffs, debuffs, conditions
- **Level / Experience**: Character progression tracking
- **Location**: Current location ID

Stats are intentionally generic. The genre/setting determines which stats matter and how they're labeled in the UI.

### Inventory

- **Items**: List of items the character possesses
  - Each item: ID, name, description, type (weapon, armor, consumable, key, misc), quantity, properties (key-value pairs for genre-specific attributes)
- **Equipment**: Currently equipped items (slots: weapon, armor, accessory, etc.)
- **Capacity**: Maximum inventory size (optional, genre-dependent)

### World

- **Locations**: Map of location ID → location data
  - Each location: ID, name, description, connections (list of connected location IDs), NPCs present, items present, visited flag
- **Current location**: Reference to the player's current location
- **Discovered locations**: Set of location IDs the player has visited or learned about
- **World flags**: Key-value pairs for tracking world state changes (e.g., "bridge_destroyed": true, "king_alive": false)

Locations are generated dynamically by the agent and added to the world state as the player explores. The initial outline seeds a set of key locations.

### Story

See [Story Engine](story-engine.md) for full specification. The state stores:

- The current story outline (premise, beats with statuses)
- The active beat index
- The story summary (condensed history of resolved beats)
- Adaptation history

### Conversation

- **History**: Ordered list of messages
  - Each message: role (player, agent, system), content, timestamp, metadata
- **Window size**: How many recent messages to include in agent context
- **Summary**: Condensed summary of older conversation history (beyond the window)

### Events

- **Recent events**: Last N events relevant to the current session (see [Event System](event-system.md))

## State Operations

### Load

Load the full game state for a session. This is done at the start of processing a player action.

### Save

Persist the full game state after a player action completes. The save is atomic — either the entire state is written or none of it is.

### Update

Partial updates to specific sections of the state. Used by tools during the agent loop:
- Update character stats
- Add/remove inventory items
- Change location
- Advance story beat
- Append conversation messages

Updates are applied in-memory during the agent loop and persisted as a batch when the action completes.

### Create

Initialize a new game state for a new session:
1. Create session metadata
2. Create character from player input
3. Generate initial world (starting location + connections)
4. Generate story outline (see [Story Engine](story-engine.md))
5. Initialize empty inventory, conversation, events
6. Persist the initial state

### Delete

Remove a session's state entirely. Irreversible.

## Schema Versioning

The state schema is versioned. When the schema changes:

1. Increment the schema version
2. Write a migration function that transforms state from version N to N+1
3. When loading state, check the version and apply migrations if needed
4. Migrations are forward-only (no downgrades)

This allows the game to evolve without breaking existing save data.

## Concurrency

Each session is independent. There is no shared mutable state between sessions. Within a session, actions are processed sequentially (one player action at a time), so there are no concurrent writes to the same session.

The persistence layer should still use row-level locking or optimistic concurrency as a safety net, but the application layer guarantees sequential access per session.

## Future Extensions

- **State snapshots**: Save checkpoints the player can revert to
- **State diffing**: Track granular changes for undo/redo
- **State streaming**: Emit state changes as a stream for real-time UI updates
- **Cross-session persistence**: Player account data that persists across games (achievements, unlocks)
