# Game State Specification

## Overview

The game state is the single source of truth for everything about a player's game. It captures the character, the world, the story, inventory, conversation history, and all other mutable data. The state is modeled with Pydantic v2 models, persisted to PostgreSQL via `asyncpg`, and loaded into memory for the duration of a player action.

## State Structure

The game state is a hierarchical Pydantic model with the following top-level sections:

```python
class GameState(BaseModel):
    session: Session
    character: Character
    inventory: Inventory
    world: World
    story: StoryState
    conversation: Conversation
    recent_events: list[GameEvent] = []
```

### Session

```python
class Session(BaseModel):
    session_id: UUID
    player_id: UUID
    created_at: datetime
    updated_at: datetime
    schema_version: int
    status: Literal["active", "paused", "completed", "abandoned"]
```

- **Session ID**: Unique identifier for this game session
- **Player ID**: The player who owns this session
- **Created at**: When the session was created
- **Updated at**: When the state was last modified
- **Schema version**: Version of the state schema (for migrations)
- **Status**: active, paused, completed, abandoned

### Character

```python
class Character(BaseModel):
    id: UUID
    name: str
    profession: str
    background: str
    stats: dict[str, float]
    status_effects: list[StatusEffect] = []
    level: int = 1
    experience: int = 0
    location_id: str
```

- **ID**: Unique character identifier
- **Name**: Player-chosen name
- **Profession/Class**: Character archetype
- **Background**: Brief character backstory (player-provided or generated)
- **Stats**: Health, max health, energy, max energy, money, and any genre-specific stats (stored as a flexible `dict[str, float]`)
- **Status effects**: Active buffs, debuffs, conditions
- **Level / Experience**: Character progression tracking
- **Location**: Current location ID

Stats are intentionally generic. The genre/setting determines which stats matter and how they're labeled in the UI.

### Inventory

```python
class Item(BaseModel):
    id: UUID
    name: str
    description: str
    item_type: Literal["weapon", "armor", "consumable", "key", "misc"]
    quantity: int = 1
    properties: dict[str, Any] = {}

class Inventory(BaseModel):
    items: list[Item] = []
    equipment: dict[str, UUID | None] = {}  # slot name → item ID
    capacity: int | None = None
```

- **Items**: List of items the character possesses
  - Each item: ID, name, description, type, quantity, properties (key-value pairs for genre-specific attributes)
- **Equipment**: Currently equipped items (slots: weapon, armor, accessory, etc.)
- **Capacity**: Maximum inventory size (optional, genre-dependent)

### World

```python
class Location(BaseModel):
    id: str
    name: str
    description: str
    connections: list[str] = []
    npcs_present: list[str] = []
    items_present: list[str] = []
    visited: bool = False

class World(BaseModel):
    locations: dict[str, Location] = {}
    current_location_id: str
    discovered_locations: set[str] = set()
    world_flags: dict[str, Any] = {}
```

- **Locations**: Map of location ID → location data
  - Each location: ID, name, description, connections (list of connected location IDs), NPCs present, items present, visited flag
- **Current location**: Reference to the player's current location
- **Discovered locations**: Set of location IDs the player has visited or learned about
- **World flags**: Key-value pairs for tracking world state changes (e.g., `"bridge_destroyed": True`, `"king_alive": False`)

Locations are generated dynamically by the agent and added to the world state as the player explores. The initial outline seeds a set of key locations.

### Story

See [Story Engine](story-engine.md) for full specification. The state stores:

- The current story outline (premise, beats with statuses)
- The active beat index
- The story summary (condensed history of resolved beats)
- Adaptation history

### Conversation

```python
class Message(BaseModel):
    role: Literal["player", "agent", "system"]
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = {}

class Conversation(BaseModel):
    history: list[Message] = []
    window_size: int = 20
    summary: str = ""
```

- **History**: Ordered list of messages
  - Each message: role (player, agent, system), content, timestamp, metadata
- **Window size**: How many recent messages to include in agent context
- **Summary**: Condensed summary of older conversation history (beyond the window)

### Events

- **Recent events**: Last N events relevant to the current session (see [Event System](event-system.md))

## State Operations

All state operations are async, designed to run within Python's asyncio event loop.

### Load

```python
async def load_game_state(pool: asyncpg.Pool, session_id: UUID) -> GameState:
    row = await pool.fetchrow("SELECT state FROM game_sessions WHERE session_id = $1", session_id)
    return GameState.model_validate_json(row["state"])
```

Load the full game state for a session. This is done at the start of processing a player action. The raw JSON from PostgreSQL is deserialized and validated through the Pydantic model.

### Save

```python
async def save_game_state(pool: asyncpg.Pool, state: GameState) -> None:
    state.session.updated_at = datetime.utcnow()
    await pool.execute(
        "UPDATE game_sessions SET state = $1, updated_at = $2 WHERE session_id = $3",
        state.model_dump_json(),
        state.session.updated_at,
        state.session.session_id,
    )
```

Persist the full game state after a player action completes. The save is atomic — either the entire state is written or none of it is. Pydantic's `model_dump_json()` serializes the full state tree.

### Update

Partial updates to specific sections of the state. Used by tools during the agent loop:
- Update character stats
- Add/remove inventory items
- Change location
- Advance story beat
- Append conversation messages

Updates are applied in-memory to the Pydantic model during the agent loop and persisted as a batch when the action completes.

### Create

Initialize a new game state for a new session:
1. Create session metadata
2. Create character from player input
3. Generate initial world (starting location + connections)
4. Generate story outline (see [Story Engine](story-engine.md))
5. Initialize empty inventory, conversation, events
6. Persist the initial state

### Delete

```python
async def delete_game_state(pool: asyncpg.Pool, session_id: UUID) -> None:
    await pool.execute("DELETE FROM game_sessions WHERE session_id = $1", session_id)
```

Remove a session's state entirely. Irreversible.

## Schema Versioning

The state schema is versioned and database migrations are managed by **Alembic**:

1. Increment the schema version in the Pydantic model
2. Generate an Alembic migration (`alembic revision --autogenerate -m "description"`)
3. Write migration logic to transform existing state data from version N to N+1
4. Apply migrations with `alembic upgrade head`
5. Migrations are forward-only (no downgrades)

For JSON state columns, the Alembic migration includes a data migration step that loads each row, transforms the JSON, and writes it back:

```python
def upgrade():
    # Schema migration
    op.add_column("game_sessions", sa.Column("schema_version", sa.Integer(), default=2))

    # Data migration for JSON state
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT session_id, state FROM game_sessions"))
    for row in rows:
        state = json.loads(row.state)
        state["session"]["schema_version"] = 2
        # ... transform state structure ...
        conn.execute(
            sa.text("UPDATE game_sessions SET state = :state WHERE session_id = :sid"),
            {"state": json.dumps(state), "sid": row.session_id},
        )
```

This allows the game to evolve without breaking existing save data.

## Concurrency

Each session is independent. There is no shared mutable state between sessions. Within a session, actions are processed sequentially (one player action at a time), so there are no concurrent writes to the same session.

Python's asyncio model is single-threaded, so within a single worker process there are no data races on in-memory state. The `asyncpg` connection pool handles concurrent database access across sessions safely.

The persistence layer should still use row-level locking (PostgreSQL `SELECT ... FOR UPDATE`) or optimistic concurrency (version column check) as a safety net, but the application layer guarantees sequential access per session.

## Future Extensions

- **State snapshots**: Save checkpoints the player can revert to
- **State diffing**: Track granular changes for undo/redo
- **State streaming**: Emit state changes as a stream for real-time UI updates
- **Cross-session persistence**: Player account data that persists across games (achievements, unlocks)
