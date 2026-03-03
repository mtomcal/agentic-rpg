"""API test fixtures — app client, WebSocket helpers, seeded sessions."""

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from agentic_rpg.events.bus import EventBus
from agentic_rpg.events.persistence import EventPersistence
from agentic_rpg.main import app
from agentic_rpg.state.manager import StateManager


# ---------------------------------------------------------------------------
# state_manager — real StateManager backed by the test DB pool
# ---------------------------------------------------------------------------
@pytest.fixture
async def state_manager(clean_db):
    """StateManager using the test database pool."""
    return StateManager(clean_db)


# ---------------------------------------------------------------------------
# api_event_bus — fresh EventBus for API tests
# ---------------------------------------------------------------------------
@pytest.fixture
def api_event_bus():
    """Fresh EventBus for API tests."""
    return EventBus()


# ---------------------------------------------------------------------------
# event_persistence — real EventPersistence backed by the test DB pool
# ---------------------------------------------------------------------------
@pytest.fixture
async def event_persistence(clean_db):
    """EventPersistence using the test database pool."""
    return EventPersistence(clean_db)


# ---------------------------------------------------------------------------
# app_client — httpx AsyncClient hitting the real FastAPI app with test DB
# ---------------------------------------------------------------------------
@pytest.fixture
async def app_client(clean_db):
    """Async HTTP client backed by the FastAPI app with a real test DB pool.

    Patches create_pool/close_pool so the app lifespan uses the test pool.
    """
    with patch("agentic_rpg.main.create_pool", return_value=clean_db), \
         patch("agentic_rpg.main.close_pool", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


# ---------------------------------------------------------------------------
# seeded_app_client — app_client with a pre-seeded session in the DB
# ---------------------------------------------------------------------------
@pytest.fixture
async def seeded_app_client(seeded_session):
    """Async HTTP client with a player + session already in the database.

    Returns (client, session_info) where session_info is the dict from
    the seeded_session fixture containing pool, player_id, session_id,
    and game_state.
    """
    pool = seeded_session["pool"]
    with patch("agentic_rpg.main.create_pool", return_value=pool), \
         patch("agentic_rpg.main.close_pool", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac, seeded_session


# ---------------------------------------------------------------------------
# player_id_header — helper to build the X-Player-ID header dict
# ---------------------------------------------------------------------------
@pytest.fixture
def player_id_header():
    """Return a function that builds the X-Player-ID header dict."""
    def _make_header(player_id: UUID) -> dict[str, str]:
        return {"X-Player-ID": str(player_id)}
    return _make_header


# ---------------------------------------------------------------------------
# mock_agent_graph — mock for the agent graph (avoids real LLM calls)
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_agent_graph():
    """A mock compiled agent graph that returns a canned response."""
    graph = AsyncMock()
    graph.ainvoke = AsyncMock(return_value={
        "messages": [
            type("Msg", (), {"content": "The tavern is quiet tonight."})()
        ]
    })
    return graph
