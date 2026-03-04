"""Smoke tests that validate the API test fixtures work correctly."""

import pytest
from httpx import AsyncClient

from agentic_rpg.events.bus import EventBus
from agentic_rpg.events.persistence import EventPersistence
from agentic_rpg.state.manager import StateManager


class TestAppClient:
    """Verify the app_client fixture provides a working HTTP client."""

    async def test_app_client_reaches_health(self, app_client):
        response = await app_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    async def test_app_client_is_async_client(self, app_client):
        assert isinstance(app_client, AsyncClient)


class TestSeededAppClient:
    """Verify the seeded_app_client fixture has DB data."""

    async def test_seeded_client_has_session(self, seeded_app_client):
        client, info = seeded_app_client
        assert "session_id" in info
        assert "player_id" in info
        assert "game_state" in info

    async def test_seeded_client_can_query_db(self, seeded_app_client):
        client, info = seeded_app_client
        pool = info["pool"]
        row = await pool.fetchrow(
            "SELECT id FROM sessions WHERE id = $1", info["session_id"]
        )
        assert row is not None
        assert row["id"] == info["session_id"]

    async def test_seeded_client_reaches_health(self, seeded_app_client):
        client, info = seeded_app_client
        response = await client.get("/health")
        assert response.status_code == 200


class TestStateManagerFixture:
    """Verify the state_manager fixture provides a working manager."""

    async def test_state_manager_type(self, state_manager):
        assert isinstance(state_manager, StateManager)

    async def test_state_manager_can_create_and_load(
        self, state_manager, sample_game_state
    ):
        await state_manager.create_session(sample_game_state)
        loaded = await state_manager.load_game_state(
            sample_game_state.session.session_id
        )
        assert loaded is not None
        assert loaded.session.session_id == sample_game_state.session.session_id
        assert loaded.character.name == "Aldric"


class TestEventFixtures:
    """Verify event bus and persistence fixtures."""

    async def test_api_event_bus_type(self, api_event_bus):
        assert isinstance(api_event_bus, EventBus)

    async def test_api_event_bus_starts_empty(self, api_event_bus):
        """A fresh EventBus has no subscribers registered."""
        # _subscribers is a defaultdict; summing its values gives total subscriber count
        total_subscribers = sum(len(v) for v in api_event_bus._subscribers.values())
        assert total_subscribers == 0

    async def test_event_persistence_type(self, event_persistence):
        assert isinstance(event_persistence, EventPersistence)

    async def test_event_persistence_has_pool(self, event_persistence, clean_db):
        """EventPersistence fixture is backed by the test pool."""
        assert event_persistence._pool is clean_db


class TestPlayerIdHeader:
    """Verify the player_id_header helper."""

    def test_builds_header_dict(self, player_id_header, sample_player_id):
        headers = player_id_header(sample_player_id)
        assert headers == {"X-Player-ID": str(sample_player_id)}

    def test_header_value_is_string(self, player_id_header, sample_player_id):
        headers = player_id_header(sample_player_id)
        assert isinstance(headers["X-Player-ID"], str)


class TestMockAgentGraph:
    """Verify the mock agent graph fixture."""

    async def test_mock_graph_returns_messages(self, mock_agent_graph):
        result = await mock_agent_graph.ainvoke({})
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "The tavern is quiet tonight."
