"""Shared test fixtures for Phase 2+ tests."""

import asyncio
from uuid import uuid4

import asyncpg
import pytest

from agentic_rpg.models.character import Character, StatusEffect, StatusEffectType
from agentic_rpg.models.events import GameEvent
from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Message,
    MessageRole,
    Session,
    SessionStatus,
)
from agentic_rpg.models.inventory import Inventory, Item, ItemType
from agentic_rpg.models.story import (
    BeatFlexibility,
    BeatStatus,
    StoryBeat,
    StoryOutline,
    StoryState,
)
from agentic_rpg.models.world import Location, World

# ---------------------------------------------------------------------------
# Database URL — tests run inside sandbox-net, so postgres hostname works.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/agentic_rpg"


# ---------------------------------------------------------------------------
# db_pool — session-scoped asyncpg connection pool
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Create a session-scoped asyncpg connection pool and run migrations."""
    pool = await asyncpg.create_pool(
        dsn=TEST_DATABASE_URL,
        min_size=2,
        max_size=5,
    )

    # Run Alembic migrations so tables exist
    conn = await pool.acquire()
    try:
        # Check if tables exist; if not, create them via raw SQL
        # (Alembic CLI may not be available in sandbox — use idempotent DDL)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
                genre TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                game_state JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                payload JSONB NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        # Create indexes to match the Alembic migration
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_player ON sessions(player_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_session_type ON events(session_id, type)"
        )
    finally:
        await pool.release(conn)

    yield pool

    await pool.close()


# ---------------------------------------------------------------------------
# clean_db — truncate all tables between tests
# ---------------------------------------------------------------------------
@pytest.fixture
async def clean_db(db_pool: asyncpg.Pool):
    """Truncate all tables before each test for isolation."""
    await db_pool.execute("TRUNCATE events, sessions, players CASCADE")
    yield db_pool


# ---------------------------------------------------------------------------
# sample IDs — consistent UUIDs for test data
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_player_id():
    """A unique player UUID for each test."""
    return uuid4()


@pytest.fixture
def sample_session_id():
    """A unique session UUID for each test."""
    return uuid4()


# ---------------------------------------------------------------------------
# sample_game_state — a fully populated GameState for testing
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_game_state(sample_session_id, sample_player_id) -> GameState:
    """Create a fully populated GameState with realistic test data."""
    return GameState(
        session=Session(
            session_id=sample_session_id,
            player_id=sample_player_id,
            status=SessionStatus.active,
            schema_version=1,
        ),
        character=Character(
            name="Aldric",
            profession="Warrior",
            background="A veteran of the Northern Wars",
            stats={
                "health": 80.0,
                "max_health": 100.0,
                "energy": 60.0,
                "max_energy": 100.0,
                "money": 50.0,
            },
            status_effects=[
                StatusEffect(
                    name="Blessed",
                    effect_type=StatusEffectType.buff,
                    description="Divine protection",
                    duration=3,
                    magnitude=1.5,
                )
            ],
            level=2,
            experience=150,
            location_id="tavern",
        ),
        inventory=Inventory(
            items=[
                Item(
                    name="Iron Sword",
                    description="A sturdy iron blade",
                    item_type=ItemType.weapon,
                    quantity=1,
                    properties={"damage": 10},
                ),
                Item(
                    name="Health Potion",
                    description="Restores 25 health",
                    item_type=ItemType.consumable,
                    quantity=3,
                    properties={"heal_amount": 25},
                ),
                Item(
                    name="Rusty Key",
                    description="Opens something old",
                    item_type=ItemType.key,
                    quantity=1,
                ),
            ],
            capacity=20,
        ),
        world=World(
            locations={
                "tavern": Location(
                    id="tavern",
                    name="The Rusty Flagon",
                    description="A dimly lit tavern smelling of ale",
                    connections=["market", "alley"],
                    npcs_present=["bartender"],
                    visited=True,
                ),
                "market": Location(
                    id="market",
                    name="Market Square",
                    description="A bustling marketplace",
                    connections=["tavern", "gate"],
                    visited=True,
                ),
                "alley": Location(
                    id="alley",
                    name="Dark Alley",
                    description="A narrow, shadowy passage",
                    connections=["tavern"],
                    visited=False,
                ),
            },
            current_location_id="tavern",
            discovered_locations={"tavern", "market"},
            world_flags={"quest_started": True},
        ),
        story=StoryState(
            outline=StoryOutline(
                premise="A warrior seeks the lost crown of the Northern Kingdom",
                setting="Medieval fantasy, dark and gritty",
                beats=[
                    StoryBeat(
                        summary="Arrive at the tavern and learn of the missing crown",
                        location="tavern",
                        key_elements=["bartender", "rumor"],
                        player_objectives=["Talk to the bartender"],
                        flexibility=BeatFlexibility.fixed,
                        status=BeatStatus.resolved,
                    ),
                    StoryBeat(
                        summary="Explore the market for clues",
                        location="market",
                        key_elements=["merchant", "map"],
                        player_objectives=["Find the map seller"],
                        flexibility=BeatFlexibility.flexible,
                        status=BeatStatus.active,
                    ),
                ],
            ),
            active_beat_index=1,
            summary="Aldric arrived at the tavern and heard rumors of the lost crown.",
        ),
        conversation=Conversation(
            history=[
                Message(
                    role=MessageRole.system,
                    content="Welcome to the adventure!",
                ),
                Message(
                    role=MessageRole.player,
                    content="I look around the tavern.",
                ),
                Message(
                    role=MessageRole.agent,
                    content="The Rusty Flagon is dimly lit. A bartender polishes mugs behind the counter.",
                ),
            ],
            window_size=20,
            summary="",
        ),
    )


# ---------------------------------------------------------------------------
# seeded_session — insert a player + session row in the DB, return IDs
# ---------------------------------------------------------------------------
@pytest.fixture
async def seeded_session(clean_db, sample_game_state) -> dict:
    """Insert a player and session into the DB, returning IDs and the pool."""
    pool = clean_db
    session = sample_game_state.session
    player_id = session.player_id
    session_id = session.session_id

    # Insert player
    await pool.execute(
        "INSERT INTO players (id) VALUES ($1)",
        player_id,
    )

    # Insert session with game_state JSONB
    game_state_json = sample_game_state.model_dump_json()
    await pool.execute(
        """INSERT INTO sessions (id, player_id, status, genre, schema_version, game_state)
           VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
        session_id,
        player_id,
        session.status.value,
        "fantasy",
        str(session.schema_version),
        game_state_json,
    )

    return {
        "pool": pool,
        "player_id": player_id,
        "session_id": session_id,
        "game_state": sample_game_state,
    }


# ---------------------------------------------------------------------------
# sample_event — a GameEvent for testing
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_event(sample_session_id) -> GameEvent:
    """Create a sample GameEvent for testing."""
    return GameEvent(
        event_type="character.stat_changed",
        payload={
            "stat_name": "health",
            "old_value": 100.0,
            "new_value": 80.0,
            "reason": "goblin attack",
        },
        source="test",
        session_id=sample_session_id,
    )


# ---------------------------------------------------------------------------
# event_bus — fresh EventBus per test
# ---------------------------------------------------------------------------
@pytest.fixture
def event_bus():
    """Return a fresh EventBus instance, isolated per test."""
    from agentic_rpg.events.bus import EventBus

    return EventBus()
