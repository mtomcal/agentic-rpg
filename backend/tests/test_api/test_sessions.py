"""Tests for session management endpoints (POST/GET/DELETE /api/v1/sessions)."""

from uuid import uuid4

import pytest


class TestCreateSession:
    """POST /api/v1/sessions"""

    async def test_create_session_returns_201(self, app_client, player_id_header):
        """Creating a session returns 201 with session_id and game_state."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {
                    "name": "Aldric",
                    "profession": "Warrior",
                    "background": "A seasoned fighter",
                },
            },
            headers=player_id_header(player_id),
        )
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "game_state" in data

    async def test_create_session_returns_correct_character(
        self, app_client, player_id_header
    ):
        """Created session preserves the character name, profession, and background."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "sci-fi",
                "character": {
                    "name": "Zara",
                    "profession": "Engineer",
                    "background": "Space mechanic",
                },
            },
            headers=player_id_header(player_id),
        )
        data = response.json()
        gs = data["game_state"]
        assert gs["character"]["name"] == "Zara"
        assert gs["character"]["profession"] == "Engineer"
        assert gs["character"]["background"] == "Space mechanic"

    async def test_create_session_sets_active_status(
        self, app_client, player_id_header
    ):
        """Newly created session has active status."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers=player_id_header(player_id),
        )
        data = response.json()
        assert data["game_state"]["session"]["status"] == "active"

    async def test_create_session_assigns_player_id(
        self, app_client, player_id_header
    ):
        """Session is scoped to the player ID from the header."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers=player_id_header(player_id),
        )
        data = response.json()
        assert data["game_state"]["session"]["player_id"] == str(player_id)

    async def test_create_session_validation_missing_genre(
        self, app_client, player_id_header
    ):
        """Missing required field 'genre' returns 422."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers=player_id_header(player_id),
        )
        assert response.status_code == 422

    async def test_create_session_validation_missing_character(
        self, app_client, player_id_header
    ):
        """Missing required field 'character' returns 422."""
        player_id = uuid4()
        response = await app_client.post(
            "/api/v1/sessions",
            json={"genre": "fantasy"},
            headers=player_id_header(player_id),
        )
        assert response.status_code == 422

    async def test_create_session_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


    async def test_create_session_invalid_player_uuid(self, app_client):
        """Invalid UUID in X-Player-ID header returns 400."""
        response = await app_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers={"X-Player-ID": "not-a-uuid"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestListSessions:
    """GET /api/v1/sessions"""

    async def test_list_sessions_empty(self, app_client, player_id_header):
        """Listing sessions for a player with no sessions returns empty list."""
        player_id = uuid4()
        response = await app_client.get(
            "/api/v1/sessions",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []

    async def test_list_sessions_returns_created(
        self, seeded_app_client, player_id_header
    ):
        """Listing sessions returns sessions belonging to the player."""
        client, info = seeded_app_client
        response = await client.get(
            "/api/v1/sessions",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        summary = data["sessions"][0]
        assert summary["session_id"] == str(info["session_id"])
        assert summary["status"] == "active"
        assert "character_name" in summary
        assert "created_at" in summary
        assert "updated_at" in summary

    async def test_list_sessions_scoped_to_player(
        self, seeded_app_client, player_id_header
    ):
        """A different player sees no sessions."""
        client, _info = seeded_app_client
        other_player = uuid4()
        response = await client.get(
            "/api/v1/sessions",
            headers=player_id_header(other_player),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []

    async def test_list_sessions_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        response = await app_client.get("/api/v1/sessions")
        assert response.status_code == 400


class TestGetSession:
    """GET /api/v1/sessions/{session_id}"""

    async def test_get_session(self, seeded_app_client, player_id_header):
        """Getting a session returns its full game state."""
        client, info = seeded_app_client
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200
        data = response.json()
        assert "game_state" in data
        gs = data["game_state"]
        assert gs["session"]["session_id"] == str(info["session_id"])
        assert gs["character"]["name"] == info["game_state"].character.name

    async def test_get_nonexistent_session(self, app_client, player_id_header):
        """Getting a non-existent session returns 404."""
        player_id = uuid4()
        fake_session = uuid4()
        response = await app_client.get(
            f"/api/v1/sessions/{fake_session}",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_get_session_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        fake_session = uuid4()
        response = await app_client.get(f"/api/v1/sessions/{fake_session}")
        assert response.status_code == 400


class TestDeleteSession:
    """DELETE /api/v1/sessions/{session_id}"""

    async def test_delete_session(self, seeded_app_client, player_id_header):
        """Deleting an existing session returns success=True."""
        client, info = seeded_app_client
        response = await client.delete(
            f"/api/v1/sessions/{info['session_id']}",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_session_actually_removes(
        self, seeded_app_client, player_id_header
    ):
        """After deletion, getting the session returns 404."""
        client, info = seeded_app_client
        await client.delete(
            f"/api/v1/sessions/{info['session_id']}",
            headers=player_id_header(info["player_id"]),
        )
        response = await client.get(
            f"/api/v1/sessions/{info['session_id']}",
            headers=player_id_header(info["player_id"]),
        )
        assert response.status_code == 404

    async def test_delete_nonexistent_session(self, app_client, player_id_header):
        """Deleting a non-existent session returns 404."""
        player_id = uuid4()
        fake_session = uuid4()
        response = await app_client.delete(
            f"/api/v1/sessions/{fake_session}",
            headers=player_id_header(player_id),
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_delete_session_missing_player_header(self, app_client):
        """Missing X-Player-ID header returns 400."""
        fake_session = uuid4()
        response = await app_client.delete(f"/api/v1/sessions/{fake_session}")
        assert response.status_code == 400
