"""Unit tests for HTTP handler functions — all DB dependencies mocked."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from agentic_rpg.main import app
from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Message,
    MessageRole,
    Session,
    SessionStatus,
)
from agentic_rpg.models.character import Character
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
# Helpers
# ---------------------------------------------------------------------------

def _make_game_state(player_id=None, session_id=None) -> GameState:
    """Build a minimal GameState for mocking."""
    if player_id is None:
        player_id = uuid4()
    if session_id is None:
        session_id = uuid4()
    return GameState(
        session=Session(
            session_id=session_id,
            player_id=player_id,
            status=SessionStatus.active,
        ),
        character=Character(
            name="Aldric",
            profession="Warrior",
            background="Veteran",
            stats={"health": 80.0, "max_health": 100.0},
        ),
        inventory=Inventory(
            items=[
                Item(
                    name="Iron Sword",
                    description="A blade",
                    item_type=ItemType.weapon,
                    quantity=1,
                )
            ]
        ),
        world=World(
            locations={
                "tavern": Location(
                    id="tavern",
                    name="The Rusty Flagon",
                    description="A dimly lit tavern",
                    connections=["market"],
                )
            },
            current_location_id="tavern",
        ),
        story=StoryState(
            outline=StoryOutline(
                premise="Seek the lost crown",
                setting="Medieval",
                beats=[
                    StoryBeat(
                        summary="Explore the market",
                        location="market",
                        key_elements=["merchant"],
                        player_objectives=["Find the map"],
                        flexibility=BeatFlexibility.flexible,
                        status=BeatStatus.active,
                    )
                ],
            ),
            active_beat_index=0,
        ),
        conversation=Conversation(
            history=[
                Message(role=MessageRole.player, content="I look around."),
                Message(role=MessageRole.agent, content="The tavern is quiet."),
            ]
        ),
    )


@pytest.fixture
def mock_state_manager():
    """Return a fully mocked StateManager."""
    return AsyncMock()


@pytest.fixture
async def unit_client(mock_state_manager):
    """HTTP client with DB pool mocked; StateManager injected via override."""
    mock_pool = AsyncMock()
    app.dependency_overrides = {}

    from agentic_rpg.api.dependencies import get_state_manager

    async def _override():
        return mock_state_manager

    app.dependency_overrides[get_state_manager] = _override

    with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
         patch("agentic_rpg.main.close_pool", return_value=None):
        app.state.db_pool = mock_pool
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides = {}


# ---------------------------------------------------------------------------
# POST /api/v1/sessions
# ---------------------------------------------------------------------------


class TestCreateSessionUnit:
    """POST /api/v1/sessions — mocked StateManager."""

    async def test_create_session_returns_201(self, unit_client, mock_state_manager):
        player_id = uuid4()
        gs = _make_game_state(player_id=player_id)
        mock_state_manager.create_session.return_value = gs

        response = await unit_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior", "background": "Vet"},
            },
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 201

    async def test_create_session_returns_session_id(self, unit_client, mock_state_manager):
        player_id = uuid4()
        gs = _make_game_state(player_id=player_id)
        mock_state_manager.create_session.return_value = gs

        response = await unit_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers={"X-Player-ID": str(player_id)},
        )

        data = response.json()
        assert data["session_id"] == str(gs.session.session_id)

    async def test_create_session_passes_character_data(self, unit_client, mock_state_manager):
        """StateManager.create_session is called with correct character data."""
        player_id = uuid4()
        gs = _make_game_state(player_id=player_id)
        mock_state_manager.create_session.return_value = gs

        await unit_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Zara", "profession": "Engineer", "background": "Mechanic"},
            },
            headers={"X-Player-ID": str(player_id)},
        )

        mock_state_manager.create_session.assert_called_once()
        call_arg: GameState = mock_state_manager.create_session.call_args[0][0]
        assert call_arg.character.name == "Zara"
        assert call_arg.character.profession == "Engineer"
        assert call_arg.character.background == "Mechanic"

    async def test_create_session_missing_character_returns_422(self, unit_client, mock_state_manager):
        player_id = uuid4()
        response = await unit_client.post(
            "/api/v1/sessions",
            json={"genre": "fantasy"},
            headers={"X-Player-ID": str(player_id)},
        )
        assert response.status_code == 422

    async def test_create_session_missing_genre_returns_422(self, unit_client, mock_state_manager):
        player_id = uuid4()
        response = await unit_client.post(
            "/api/v1/sessions",
            json={"character": {"name": "Aldric", "profession": "Warrior"}},
            headers={"X-Player-ID": str(player_id)},
        )
        assert response.status_code == 422

    async def test_create_session_missing_player_header_returns_400(self, unit_client, mock_state_manager):
        response = await unit_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "Missing X-Player-ID header"

    async def test_create_session_invalid_uuid_returns_400(self, unit_client, mock_state_manager):
        response = await unit_client.post(
            "/api/v1/sessions",
            json={
                "genre": "fantasy",
                "character": {"name": "Aldric", "profession": "Warrior"},
            },
            headers={"X-Player-ID": "not-a-uuid"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid X-Player-ID header" in data["detail"]["error"]


# ---------------------------------------------------------------------------
# GET /api/v1/sessions
# ---------------------------------------------------------------------------


class TestListSessionsUnit:
    """GET /api/v1/sessions — mocked StateManager."""

    async def test_list_sessions_empty(self, unit_client, mock_state_manager):
        player_id = uuid4()
        mock_state_manager.list_sessions.return_value = []

        response = await unit_client.get(
            "/api/v1/sessions",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []

    async def test_list_sessions_returns_summaries(self, unit_client, mock_state_manager):
        player_id = uuid4()
        gs = _make_game_state(player_id=player_id)
        mock_state_manager.list_sessions.return_value = [gs]

        response = await unit_client.get(
            "/api/v1/sessions",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        summary = data["sessions"][0]
        assert summary["session_id"] == str(gs.session.session_id)
        assert summary["character_name"] == "Aldric"
        assert summary["status"] == "active"

    async def test_list_sessions_missing_header_returns_400(self, unit_client, mock_state_manager):
        response = await unit_client.get("/api/v1/sessions")
        assert response.status_code == 400

    async def test_list_sessions_passes_player_id_to_manager(self, unit_client, mock_state_manager):
        player_id = uuid4()
        mock_state_manager.list_sessions.return_value = []

        await unit_client.get(
            "/api/v1/sessions",
            headers={"X-Player-ID": str(player_id)},
        )

        mock_state_manager.list_sessions.assert_called_once_with(player_id)


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}
# ---------------------------------------------------------------------------


class TestGetSessionUnit:
    """GET /api/v1/sessions/{session_id} — mocked StateManager."""

    async def test_get_session_success(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["game_state"]["session"]["session_id"] == str(session_id)
        assert data["game_state"]["character"]["name"] == "Aldric"

    async def test_get_session_not_found_returns_404(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.load_game_state.return_value = None

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "session_not_found"

    async def test_get_session_missing_header_returns_400(self, unit_client, mock_state_manager):
        session_id = uuid4()
        response = await unit_client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /api/v1/sessions/{session_id}
# ---------------------------------------------------------------------------


class TestDeleteSessionUnit:
    """DELETE /api/v1/sessions/{session_id} — mocked StateManager."""

    async def test_delete_session_success(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.delete_game_state.return_value = True

        response = await unit_client.delete(
            f"/api/v1/sessions/{session_id}",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_session_not_found_returns_404(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.delete_game_state.return_value = False

        response = await unit_client.delete(
            f"/api/v1/sessions/{session_id}",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "session_not_found"

    async def test_delete_session_missing_header_returns_400(self, unit_client, mock_state_manager):
        session_id = uuid4()
        response = await unit_client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/state
# ---------------------------------------------------------------------------


class TestGetStateSummaryUnit:
    """GET /sessions/{session_id}/state — mocked StateManager."""

    async def test_get_state_summary_success(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["character"]["name"] == "Aldric"
        assert data["character"]["profession"] == "Warrior"
        assert data["character"]["level"] == 1
        assert data["character"]["health"] == 80.0
        assert data["character"]["max_health"] == 100.0

    async def test_get_state_summary_location(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        data = response.json()
        assert data["location"]["id"] == "tavern"
        assert data["location"]["name"] == "The Rusty Flagon"
        assert "market" in data["location"]["connections"]

    async def test_get_state_summary_story_beat(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        data = response.json()
        assert data["story_beat"] is not None
        assert data["story_beat"]["summary"] == "Explore the market"
        assert data["story_beat"]["status"] == "active"

    async def test_get_state_summary_no_location_in_world(self, unit_client, mock_state_manager):
        """When current_location_id is not in locations dict, fallback location is returned."""
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        # Remove the current location from the world so the fallback branch is taken
        gs.world.locations = {}
        gs.world.current_location_id = "unknown_place"
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location"]["id"] == "unknown_place"
        assert data["location"]["name"] == "unknown_place"
        assert data["location"]["description"] == ""

    async def test_get_state_summary_no_beats(self, unit_client, mock_state_manager):
        """When story has no beats, story_beat is None."""
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        gs.story.outline = None
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["story_beat"] is None

    async def test_get_state_summary_not_found_returns_404(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.load_game_state.return_value = None

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/state",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "session_not_found"


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/inventory
# ---------------------------------------------------------------------------


class TestGetInventoryUnit:
    """GET /sessions/{session_id}/inventory — mocked StateManager."""

    async def test_get_inventory_success(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/inventory",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Iron Sword"

    async def test_get_inventory_not_found_returns_404(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.load_game_state.return_value = None

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/inventory",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "session_not_found"


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/history
# ---------------------------------------------------------------------------


class TestGetHistoryUnit:
    """GET /sessions/{session_id}/history — mocked StateManager."""

    async def test_get_history_success(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/history",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "I look around."
        assert data["messages"][1]["content"] == "The tavern is quiet."

    async def test_get_history_pagination_limit(self, unit_client, mock_state_manager):
        """Limit parameter restricts number of returned messages."""
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/history?limit=1",
            headers={"X-Player-ID": str(player_id)},
        )

        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "I look around."

    async def test_get_history_pagination_offset(self, unit_client, mock_state_manager):
        """Offset parameter skips messages."""
        player_id = uuid4()
        session_id = uuid4()
        gs = _make_game_state(player_id=player_id, session_id=session_id)
        mock_state_manager.load_game_state.return_value = gs

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/history?offset=1",
            headers={"X-Player-ID": str(player_id)},
        )

        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "The tavern is quiet."

    async def test_get_history_not_found_returns_404(self, unit_client, mock_state_manager):
        player_id = uuid4()
        session_id = uuid4()
        mock_state_manager.load_game_state.return_value = None

        response = await unit_client.get(
            f"/api/v1/sessions/{session_id}/history",
            headers={"X-Player-ID": str(player_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "session_not_found"
