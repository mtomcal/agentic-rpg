"""WebSocket endpoint tests — RED phase."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from starlette.testclient import TestClient

from agentic_rpg.api.websocket import ConnectionHub
from agentic_rpg.main import app
from agentic_rpg.models.character import Character
from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Session,
    SessionStatus,
)
from agentic_rpg.models.world import Location, World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PLAYER_ID = uuid4()
SESSION_ID = uuid4()


def _make_game_state() -> GameState:
    """Create a minimal GameState for WebSocket tests."""
    return GameState(
        session=Session(
            session_id=SESSION_ID,
            player_id=PLAYER_ID,
            status=SessionStatus.active,
        ),
        character=Character(
            name="Aldric",
            profession="Warrior",
            background="Test background",
        ),
        world=World(
            locations={
                "tavern": Location(
                    id="tavern",
                    name="The Rusty Flagon",
                    description="A dimly lit tavern",
                    connections=["market"],
                ),
            },
            current_location_id="tavern",
        ),
        conversation=Conversation(),
    )


@pytest.fixture
def ws_client():
    """TestClient with mocked DB pool for WebSocket tests."""
    app.state.db_pool = MagicMock()
    return TestClient(app)


@pytest.fixture
def mock_state_manager():
    """Patch StateManager to avoid real DB calls during WebSocket tests."""
    game_state = _make_game_state()
    mock_sm = AsyncMock()
    mock_sm.load_game_state = AsyncMock(return_value=game_state)
    with patch("agentic_rpg.api.websocket.StateManager", return_value=mock_sm) as p:
        yield mock_sm


@pytest.fixture
def mock_state_manager_no_session():
    """Patch StateManager to return None (session not found)."""
    mock_sm = AsyncMock()
    mock_sm.load_game_state = AsyncMock(return_value=None)
    with patch("agentic_rpg.api.websocket.StateManager", return_value=mock_sm):
        yield mock_sm


# ---------------------------------------------------------------------------
# ConnectionHub unit tests
# ---------------------------------------------------------------------------


class TestConnectionHub:
    """Unit tests for the WebSocket ConnectionHub."""

    def test_register_stores_connection(self):
        hub = ConnectionHub()
        ws = MagicMock()
        hub.register("session-1", ws)
        assert hub.get("session-1") is ws

    def test_unregister_removes_connection(self):
        hub = ConnectionHub()
        ws = MagicMock()
        hub.register("session-1", ws)
        hub.unregister("session-1")
        assert hub.get("session-1") is None

    def test_unregister_nonexistent_is_noop(self):
        hub = ConnectionHub()
        hub.unregister("no-such-session")
        assert hub.get("no-such-session") is None
        assert hub.active_count == 0

    def test_register_replaces_existing(self):
        hub = ConnectionHub()
        ws1 = MagicMock()
        ws2 = MagicMock()
        hub.register("session-1", ws1)
        hub.register("session-1", ws2)
        assert hub.get("session-1") is ws2

    @pytest.mark.asyncio
    async def test_send_json_to_registered_connection(self):
        hub = ConnectionHub()
        ws = AsyncMock()
        hub.register("session-1", ws)
        msg = {"type": "test", "data": {}}
        await hub.send_json("session-1", msg)
        ws.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_send_json_to_unknown_session_is_noop(self):
        hub = ConnectionHub()
        # Should not raise
        await hub.send_json("no-such-session", {"type": "test"})

    def test_active_connections_count(self):
        hub = ConnectionHub()
        assert hub.active_count == 0
        hub.register("s1", MagicMock())
        assert hub.active_count == 1
        hub.register("s2", MagicMock())
        assert hub.active_count == 2
        hub.unregister("s1")
        assert hub.active_count == 1


# ---------------------------------------------------------------------------
# WebSocket endpoint integration tests
# ---------------------------------------------------------------------------


class TestWebSocketConnect:
    """Tests for the WebSocket connection handshake."""

    def test_connect_sends_connected_message(self, ws_client, mock_state_manager):
        """On successful connection, server sends a 'connected' message."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["data"]["session_id"] == str(SESSION_ID)
            game_state = data["data"]["game_state"]
            assert game_state["character"]["name"] == "Aldric"
            assert game_state["character"]["profession"] == "Warrior"
            assert game_state["world"]["current_location_id"] == "tavern"
            assert game_state["world"]["locations"]["tavern"]["name"] == "The Rusty Flagon"
            assert "timestamp" in data

    def test_connect_invalid_session_sends_error(self, ws_client, mock_state_manager_no_session):
        """Connecting with a non-existent session ID sends error and closes."""
        fake_session = uuid4()
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{fake_session}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["data"]["code"] == "session_not_found"

    def test_connect_missing_player_id_sends_error(self, ws_client, mock_state_manager):
        """Connecting without X-Player-ID header sends error and closes."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["data"]["code"] == "missing_player_id"

    def test_connect_with_player_id_query_param(self, ws_client, mock_state_manager):
        """Connecting with player_id as query param (browser WebSocket fallback) succeeds."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws?player_id={PLAYER_ID}",
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            assert data["data"]["session_id"] == str(SESSION_ID)
            assert data["data"]["game_state"]["character"]["name"] == "Aldric"

    def test_connect_with_invalid_query_param_player_id(self, ws_client, mock_state_manager):
        """Connecting with invalid player_id query param sends error."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws?player_id=not-a-uuid",
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["data"]["code"] == "invalid_player_id"

    def test_connect_invalid_player_id_sends_error(self, ws_client, mock_state_manager):
        """Connecting with a non-UUID X-Player-ID sends error and closes."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": "not-a-valid-uuid"},
        ) as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["data"]["code"] == "invalid_player_id"

    def test_connect_with_nonexistent_location_sends_full_state(self, ws_client):
        """If current_location_id is not in locations map, full game state is still sent."""
        gs = _make_game_state()
        gs.world.current_location_id = "unknown_place"
        mock_sm = AsyncMock()
        mock_sm.load_game_state = AsyncMock(return_value=gs)
        with patch("agentic_rpg.api.websocket.StateManager", return_value=mock_sm):
            with ws_client.websocket_connect(
                f"/api/v1/sessions/{SESSION_ID}/ws",
                headers={"X-Player-ID": str(PLAYER_ID)},
            ) as ws:
                data = ws.receive_json()
                assert data["type"] == "connected"
                game_state = data["data"]["game_state"]
                assert game_state["world"]["current_location_id"] == "unknown_place"


class TestWebSocketPlayerAction:
    """Tests for handling player_action messages."""

    def test_player_action_triggers_agent_response(self, ws_client, mock_state_manager):
        """Sending a player_action produces an agent_response."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content="The tavern is quiet tonight.")]
        })

        with patch(
            "agentic_rpg.api.websocket.build_agent_graph",
            return_value=mock_graph,
        ), patch(
            "agentic_rpg.api.websocket.get_tools_and_model",
            return_value=([], MagicMock()),
        ):
            with ws_client.websocket_connect(
                f"/api/v1/sessions/{SESSION_ID}/ws",
                headers={"X-Player-ID": str(PLAYER_ID)},
            ) as ws:
                connected = ws.receive_json()
                assert connected["type"] == "connected"

                ws.send_json({
                    "type": "player_action",
                    "data": {"text": "I look around the tavern."},
                })

                response = ws.receive_json()
                assert response["type"] == "agent_response"
                assert response["data"]["text"] == "The tavern is quiet tonight."
                assert response["data"]["is_complete"] is True

    def test_player_action_missing_text_returns_error(self, ws_client, mock_state_manager):
        """Player action without text field returns an error."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            ws.send_json({"type": "player_action", "data": {}})
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_request"
            assert "text" in error["data"]["message"].lower()

    def test_agent_error_sends_error_message(self, ws_client, mock_state_manager):
        """If the agent graph raises, client gets an error message."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("LLM exploded"))

        with patch(
            "agentic_rpg.api.websocket.build_agent_graph",
            return_value=mock_graph,
        ), patch(
            "agentic_rpg.api.websocket.get_tools_and_model",
            return_value=([], MagicMock()),
        ):
            with ws_client.websocket_connect(
                f"/api/v1/sessions/{SESSION_ID}/ws",
                headers={"X-Player-ID": str(PLAYER_ID)},
            ) as ws:
                connected = ws.receive_json()
                assert connected["type"] == "connected"

                ws.send_json({
                    "type": "player_action",
                    "data": {"text": "I attack the dragon."},
                })

                error = ws.receive_json()
                assert error["type"] == "error"
                assert error["data"]["code"] == "agent_error"
                assert "Failed to process action" in error["data"]["message"]


class TestWebSocketMessageHandling:
    """Tests for various message types and error handling."""

    def test_invalid_message_type_returns_error(self, ws_client, mock_state_manager):
        """Sending an unknown message type returns an error message."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            ws.send_json({"type": "unknown_type", "data": {}})
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_message_type"

    def test_malformed_json_returns_error(self, ws_client, mock_state_manager):
        """Sending non-JSON data returns an error message."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            ws.send_text("not valid json {{{")
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_message"

    def test_pong_message_accepted_silently(self, ws_client, mock_state_manager):
        """Sending a pong message should not cause an error."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            # Send pong — should be silently accepted
            ws.send_json({"type": "pong", "data": {}})

            # Send another message to confirm connection is alive
            ws.send_json({"type": "unknown_type", "data": {}})
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_message_type"

    def test_empty_text_in_player_action_returns_error(self, ws_client, mock_state_manager):
        """Player action with empty string text returns an error."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            ws.send_json({"type": "player_action", "data": {"text": ""}})
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_request"

    def test_non_dict_data_in_player_action_returns_error(self, ws_client, mock_state_manager):
        """Player action with non-dict data field returns an error."""
        with ws_client.websocket_connect(
            f"/api/v1/sessions/{SESSION_ID}/ws",
            headers={"X-Player-ID": str(PLAYER_ID)},
        ) as ws:
            connected = ws.receive_json()
            assert connected["type"] == "connected"

            ws.send_json({"type": "player_action", "data": "string-not-dict"})
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["data"]["code"] == "invalid_request"
