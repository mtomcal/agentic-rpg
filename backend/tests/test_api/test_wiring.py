"""Tests for main.py wiring — lifespan, error handling, dependencies, middleware."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from agentic_rpg.api.middleware import GameError
from agentic_rpg.events.bus import EventBus
from agentic_rpg.events.persistence import EventPersistence
from agentic_rpg.main import app, lifespan
from agentic_rpg.state.manager import StateManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
async def wired_client(clean_db):
    """Async HTTP client with the fully wired app and test DB pool."""
    with patch("agentic_rpg.main.create_pool", return_value=clean_db), \
         patch("agentic_rpg.main.close_pool", return_value=None):
        app.state.db_pool = clean_db
        app.state.event_bus = EventBus()
        app.state.event_persistence = EventPersistence(clean_db)
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


# ---------------------------------------------------------------------------
# Lifespan wiring — event_bus and event_persistence on app.state
# ---------------------------------------------------------------------------


class TestLifespanWiring:
    """Test that the lifespan context manager sets up all app.state attributes."""

    async def test_lifespan_creates_db_pool(self):
        """Lifespan should set app.state.db_pool from create_pool."""
        test_app = FastAPI()
        mock_pool = AsyncMock()
        with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            async with lifespan(test_app):
                assert test_app.state.db_pool is mock_pool

    async def test_lifespan_creates_event_bus(self):
        """Lifespan should set app.state.event_bus as an EventBus instance."""
        test_app = FastAPI()
        mock_pool = AsyncMock()
        with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            async with lifespan(test_app):
                assert isinstance(test_app.state.event_bus, EventBus)

    async def test_lifespan_creates_event_persistence(self):
        """Lifespan should set app.state.event_persistence as an EventPersistence."""
        test_app = FastAPI()
        mock_pool = AsyncMock()
        with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
             patch("agentic_rpg.main.close_pool", return_value=None):
            async with lifespan(test_app):
                assert isinstance(test_app.state.event_persistence, EventPersistence)

    async def test_lifespan_calls_close_pool_on_shutdown(self):
        """Lifespan should call close_pool with the db_pool on shutdown."""
        test_app = FastAPI()
        mock_pool = AsyncMock()
        with patch("agentic_rpg.main.create_pool", return_value=mock_pool), \
             patch("agentic_rpg.main.close_pool", return_value=None) as mock_close:
            async with lifespan(test_app):
                pass
            mock_close.assert_called_once_with(mock_pool)

    async def test_health_still_works_with_full_wiring(self, wired_client):
        """Health endpoint works with the fully wired app."""
        response = await wired_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GameError exception handler
# ---------------------------------------------------------------------------


class TestGameErrorHandler:
    """Test the custom GameError exception handler returns structured errors."""

    async def test_game_error_returns_correct_status(self, wired_client):
        """GameError with status_code=404 should return 404."""
        @app.get("/test-game-error")
        async def _raise_game_error():
            raise GameError(code="test_error", message="Something went wrong", status_code=404)

        response = await wired_client.get("/test-game-error")
        assert response.status_code == 404
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-game-error"]

    async def test_game_error_returns_structured_body(self, wired_client):
        """GameError should return {error: {code, message}} JSON."""
        @app.get("/test-game-error-body")
        async def _raise_game_error():
            raise GameError(code="session_not_found", message="Session not found", status_code=404)

        response = await wired_client.get("/test-game-error-body")
        data = response.json()
        assert data == {
            "error": {
                "code": "session_not_found",
                "message": "Session not found",
            }
        }
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-game-error-body"]

    async def test_game_error_default_status_is_400(self, wired_client):
        """GameError with no explicit status_code defaults to 400."""
        @app.get("/test-game-error-default")
        async def _raise_game_error():
            raise GameError(code="invalid_request", message="Bad request")

        response = await wired_client.get("/test-game-error-default")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "invalid_request"
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-game-error-default"]


# ---------------------------------------------------------------------------
# Dependency injection functions
# ---------------------------------------------------------------------------


class TestDependencyFunctions:
    """Test that dependency injection functions return correct objects."""

    async def test_get_db_pool_returns_pool(self, wired_client):
        """get_db_pool should return the db_pool from app.state."""
        from agentic_rpg.api.dependencies import get_db_pool

        mock_request = MagicMock()
        mock_request.app.state.db_pool = app.state.db_pool
        result = await get_db_pool(mock_request)
        assert result is app.state.db_pool

    async def test_get_state_manager_returns_state_manager(self, wired_client):
        """get_state_manager should return a StateManager wrapping the db_pool."""
        from agentic_rpg.api.dependencies import get_state_manager

        mock_request = MagicMock()
        mock_request.app.state.db_pool = app.state.db_pool
        result = await get_state_manager(mock_request)
        assert isinstance(result, StateManager)

    async def test_get_event_bus_returns_event_bus(self, wired_client):
        """get_event_bus should return the EventBus from app.state."""
        from agentic_rpg.api.dependencies import get_event_bus

        mock_request = MagicMock()
        mock_request.app.state.event_bus = app.state.event_bus
        result = await get_event_bus(mock_request)
        assert result is app.state.event_bus

    async def test_get_event_persistence_returns_event_persistence(self, wired_client):
        """get_event_persistence should return the EventPersistence from app.state."""
        from agentic_rpg.api.dependencies import get_event_persistence

        mock_request = MagicMock()
        mock_request.app.state.event_persistence = app.state.event_persistence
        result = await get_event_persistence(mock_request)
        assert result is app.state.event_persistence


# ---------------------------------------------------------------------------
# get_current_player dependency
# ---------------------------------------------------------------------------


class TestGetCurrentPlayer:
    """Test the X-Player-ID header extraction dependency."""

    async def test_valid_uuid_returns_uuid(self):
        """A valid UUID string should be returned as a UUID object."""
        from agentic_rpg.api.dependencies import get_current_player

        player_uuid = uuid4()
        result = await get_current_player(x_player_id=str(player_uuid))
        assert result == player_uuid
        assert isinstance(result, UUID)

    async def test_missing_header_raises_400(self):
        """Missing X-Player-ID should raise HTTPException with 400."""
        from agentic_rpg.api.dependencies import get_current_player

        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id=None)
        assert exc_info.value.status_code == 400
        assert "Missing X-Player-ID" in str(exc_info.value.detail)

    async def test_invalid_uuid_raises_400(self):
        """Invalid UUID string should raise HTTPException with 400."""
        from agentic_rpg.api.dependencies import get_current_player

        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id="not-a-uuid")
        assert exc_info.value.status_code == 400
        assert "Invalid X-Player-ID" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# GameError class
# ---------------------------------------------------------------------------


class TestGameError:
    """Test the GameError exception class itself."""

    def test_game_error_stores_code(self):
        err = GameError(code="test", message="msg")
        assert err.code == "test"

    def test_game_error_stores_message(self):
        err = GameError(code="test", message="Something bad")
        assert err.message == "Something bad"

    def test_game_error_default_status_code(self):
        err = GameError(code="test", message="msg")
        assert err.status_code == 400

    def test_game_error_custom_status_code(self):
        err = GameError(code="not_found", message="msg", status_code=404)
        assert err.status_code == 404
