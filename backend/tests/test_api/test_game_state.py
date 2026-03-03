"""Tests for game state sub-endpoints under /api/v1/sessions/{session_id}/."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from agentic_rpg.main import app
from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Session,
    SessionStatus,
)
from agentic_rpg.models.character import Character
from agentic_rpg.models.story import StoryState, StoryOutline, StoryBeat, BeatStatus
from agentic_rpg.models.world import Location, World
from httpx import ASGITransport, AsyncClient


class TestGetStateSummary:
    """GET /api/v1/sessions/{session_id}/state"""

    async def test_state_summary_returns_200(self, seeded_app_client, player_id_header):
        """Getting state summary for a valid session returns 200."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/state",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200

    async def test_state_summary_has_character(self, seeded_app_client, player_id_header):
        """State summary includes character summary with name, profession, level, stats."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/state",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        char = data["character"]
        assert char["name"] == "Aldric"
        assert char["profession"] == "Warrior"
        assert char["level"] == 2
        assert char["health"] == 80.0
        assert char["max_health"] == 100.0

    async def test_state_summary_has_location(self, seeded_app_client, player_id_header):
        """State summary includes location summary with id, name, description."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/state",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        loc = data["location"]
        assert loc["id"] == "tavern"
        assert loc["name"] == "The Rusty Flagon"
        assert loc["description"] == "A dimly lit tavern smelling of ale"
        assert loc["connections"] == ["market", "alley"]

    async def test_state_summary_has_story_beat(self, seeded_app_client, player_id_header):
        """State summary includes the active story beat summary."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/state",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        beat = data["story_beat"]
        assert beat["summary"] == "Explore the market for clues"
        assert beat["status"] == "active"
        assert beat["location"] == "market"

    async def test_state_summary_nonexistent_session(self, app_client, player_id_header):
        """Getting state summary for a non-existent session returns 404."""
        player_id = uuid4()
        fake_session = uuid4()
        response = await app_client.get(
            f"/api/v1/sessions/{fake_session}/state",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_state_summary_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        fake_session = uuid4()
        response = await app_client.get(f"/api/v1/sessions/{fake_session}/state")
        assert response.status_code == 400

    async def test_state_summary_missing_location_fallback(self, clean_db, player_id_header):
        """When current_location_id is not in locations dict, returns fallback location."""
        player_id = uuid4()
        gs = GameState(
            session=Session(player_id=player_id, status=SessionStatus.active),
            character=Character(name="Test", profession="Mage"),
            world=World(current_location_id="unknown", locations={}),
        )
        pool = clean_db
        # Insert player + session
        await pool.execute("INSERT INTO players (id) VALUES ($1)", player_id)
        await pool.execute(
            """INSERT INTO sessions (id, player_id, status, genre, schema_version, game_state)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
            gs.session.session_id, player_id, "active", "fantasy", "1",
            gs.model_dump_json(),
        )
        with patch("agentic_rpg.main.create_pool", return_value=pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            app.state.db_pool = pool
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    f"/api/v1/sessions/{gs.session.session_id}/state",
                    headers=player_id_header(player_id),
                )
        assert response.status_code == 200
        loc = response.json()["location"]
        assert loc["id"] == "unknown"
        assert loc["name"] == "unknown"
        assert loc["connections"] == []

    async def test_state_summary_no_story_outline(self, clean_db, player_id_header):
        """When story outline is None, story_beat is None."""
        player_id = uuid4()
        gs = GameState(
            session=Session(player_id=player_id, status=SessionStatus.active),
            character=Character(name="Test", profession="Mage"),
            story=StoryState(outline=None),
        )
        pool = clean_db
        await pool.execute("INSERT INTO players (id) VALUES ($1)", player_id)
        await pool.execute(
            """INSERT INTO sessions (id, player_id, status, genre, schema_version, game_state)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
            gs.session.session_id, player_id, "active", "fantasy", "1",
            gs.model_dump_json(),
        )
        with patch("agentic_rpg.main.create_pool", return_value=pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            app.state.db_pool = pool
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    f"/api/v1/sessions/{gs.session.session_id}/state",
                    headers=player_id_header(player_id),
                )
        assert response.status_code == 200
        assert response.json()["story_beat"] is None

    async def test_state_summary_beat_index_out_of_range(self, clean_db, player_id_header):
        """When active_beat_index is out of bounds, story_beat is None."""
        player_id = uuid4()
        gs = GameState(
            session=Session(player_id=player_id, status=SessionStatus.active),
            character=Character(name="Test", profession="Mage"),
            story=StoryState(
                outline=StoryOutline(
                    premise="test", setting="test",
                    beats=[StoryBeat(summary="Only beat", location="here", status=BeatStatus.planned)],
                ),
                active_beat_index=99,  # out of range
            ),
        )
        pool = clean_db
        await pool.execute("INSERT INTO players (id) VALUES ($1)", player_id)
        await pool.execute(
            """INSERT INTO sessions (id, player_id, status, genre, schema_version, game_state)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb)""",
            gs.session.session_id, player_id, "active", "fantasy", "1",
            gs.model_dump_json(),
        )
        with patch("agentic_rpg.main.create_pool", return_value=pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            app.state.db_pool = pool
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                response = await ac.get(
                    f"/api/v1/sessions/{gs.session.session_id}/state",
                    headers=player_id_header(player_id),
                )
        assert response.status_code == 200
        assert response.json()["story_beat"] is None


class TestGetInventory:
    """GET /api/v1/sessions/{session_id}/inventory"""

    async def test_inventory_returns_200(self, seeded_app_client, player_id_header):
        """Getting inventory for a valid session returns 200."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/inventory",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200

    async def test_inventory_returns_items(self, seeded_app_client, player_id_header):
        """Inventory response contains the correct items."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/inventory",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert len(data["items"]) == 3
        item_names = [item["name"] for item in data["items"]]
        assert "Iron Sword" in item_names
        assert "Health Potion" in item_names
        assert "Rusty Key" in item_names

    async def test_inventory_item_details(self, seeded_app_client, player_id_header):
        """Inventory items have the expected fields and values."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/inventory",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        sword = next(i for i in data["items"] if i["name"] == "Iron Sword")
        assert sword["item_type"] == "weapon"
        assert sword["quantity"] == 1
        assert sword["description"] == "A sturdy iron blade"

    async def test_inventory_has_equipment(self, seeded_app_client, player_id_header):
        """Inventory response includes the equipment dict matching seeded data."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/inventory",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert data["equipment"] == {}

    async def test_inventory_nonexistent_session(self, app_client, player_id_header):
        """Getting inventory for a non-existent session returns 404."""
        player_id = uuid4()
        fake_session = uuid4()
        response = await app_client.get(
            f"/api/v1/sessions/{fake_session}/inventory",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_inventory_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        fake_session = uuid4()
        response = await app_client.get(f"/api/v1/sessions/{fake_session}/inventory")
        assert response.status_code == 400


class TestGetHistory:
    """GET /api/v1/sessions/{session_id}/history"""

    async def test_history_returns_200(self, seeded_app_client, player_id_header):
        """Getting conversation history returns 200."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200

    async def test_history_returns_messages(self, seeded_app_client, player_id_header):
        """History response contains messages and total count."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert data["total"] == 3
        assert len(data["messages"]) == 3

    async def test_history_message_content(self, seeded_app_client, player_id_header):
        """Messages contain role and content fields."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        messages = data["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Welcome to the adventure!"
        assert messages[1]["role"] == "player"
        assert messages[1]["content"] == "I look around the tavern."
        assert messages[2]["role"] == "agent"

    async def test_history_pagination_limit(self, seeded_app_client, player_id_header):
        """Limit query param restricts the number of messages returned."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history?limit=2",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["total"] == 3  # total is still the full count

    async def test_history_pagination_offset(self, seeded_app_client, player_id_header):
        """Offset query param skips messages from the start."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history?offset=1&limit=10",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert len(data["messages"]) == 2  # 3 total, skip 1
        assert data["messages"][0]["role"] == "player"
        assert data["total"] == 3

    async def test_history_pagination_offset_beyond(self, seeded_app_client, player_id_header):
        """Offset beyond the total returns empty messages list."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}/history?offset=100",
            headers=player_id_header(info["player_id"]),
        )
        data = response.json()
        assert len(data["messages"]) == 0
        assert data["total"] == 3

    async def test_history_nonexistent_session(self, app_client, player_id_header):
        """Getting history for a non-existent session returns 404."""
        player_id = uuid4()
        fake_session = uuid4()
        response = await app_client.get(
            f"/api/v1/sessions/{fake_session}/history",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_history_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        fake_session = uuid4()
        response = await app_client.get(f"/api/v1/sessions/{fake_session}/history")
        assert response.status_code == 400
