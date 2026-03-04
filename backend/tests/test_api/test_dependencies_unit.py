"""Unit tests for API dependency injection functions."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from agentic_rpg.api.dependencies import (
    get_current_player,
    get_db_pool,
    get_event_bus,
    get_event_persistence,
    get_state_manager,
)
from agentic_rpg.events.bus import EventBus
from agentic_rpg.events.persistence import EventPersistence
from agentic_rpg.state.manager import StateManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(db_pool=None, event_bus=None, event_persistence=None):
    """Build a fake Request-like object with app.state populated."""
    mock_request = MagicMock()
    mock_request.app.state.db_pool = db_pool or AsyncMock()
    mock_request.app.state.event_bus = event_bus or EventBus()
    mock_request.app.state.event_persistence = event_persistence or MagicMock()
    return mock_request


# ---------------------------------------------------------------------------
# get_db_pool
# ---------------------------------------------------------------------------


class TestGetDbPool:
    async def test_returns_pool_from_app_state(self):
        mock_pool = AsyncMock()
        request = _make_request(db_pool=mock_pool)

        result = await get_db_pool(request)

        assert result is mock_pool

    async def test_returns_exact_same_object(self):
        """The pool returned is the exact same object, not a copy."""
        sentinel = object()
        request = _make_request(db_pool=sentinel)

        result = await get_db_pool(request)

        assert result is sentinel


# ---------------------------------------------------------------------------
# get_state_manager
# ---------------------------------------------------------------------------


class TestGetStateManager:
    async def test_returns_state_manager_instance(self):
        mock_pool = AsyncMock()
        request = _make_request(db_pool=mock_pool)

        result = await get_state_manager(request)

        assert isinstance(result, StateManager)

    async def test_state_manager_wraps_pool(self):
        """StateManager is constructed with the pool from app state."""
        mock_pool = AsyncMock()
        request = _make_request(db_pool=mock_pool)

        result = await get_state_manager(request)

        # StateManager stores the pool as _pool — verify it's the correct one
        assert result._pool is mock_pool


# ---------------------------------------------------------------------------
# get_event_bus
# ---------------------------------------------------------------------------


class TestGetEventBus:
    async def test_returns_event_bus_from_app_state(self):
        bus = EventBus()
        request = _make_request(event_bus=bus)

        result = await get_event_bus(request)

        assert result is bus

    async def test_returns_event_bus_instance(self):
        bus = EventBus()
        request = _make_request(event_bus=bus)

        result = await get_event_bus(request)

        assert isinstance(result, EventBus)


# ---------------------------------------------------------------------------
# get_event_persistence
# ---------------------------------------------------------------------------


class TestGetEventPersistence:
    async def test_returns_event_persistence_from_app_state(self):
        mock_pool = AsyncMock()
        persistence = EventPersistence(mock_pool)
        request = _make_request(event_persistence=persistence)

        result = await get_event_persistence(request)

        assert result is persistence

    async def test_returns_exact_object(self):
        """The persistence object returned is identical to the one on app state."""
        sentinel = MagicMock(spec=EventPersistence)
        request = _make_request(event_persistence=sentinel)

        result = await get_event_persistence(request)

        assert result is sentinel


# ---------------------------------------------------------------------------
# get_current_player
# ---------------------------------------------------------------------------


class TestGetCurrentPlayer:
    async def test_valid_uuid_header_returns_uuid(self):
        player_id = uuid4()

        result = await get_current_player(x_player_id=str(player_id))

        assert result == player_id
        assert isinstance(result, UUID)

    async def test_missing_header_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id=None)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"] == "Missing X-Player-ID header"

    async def test_invalid_uuid_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id="not-a-uuid")

        assert exc_info.value.status_code == 400
        assert "Invalid X-Player-ID header" in exc_info.value.detail["error"]

    async def test_empty_string_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id="")

        assert exc_info.value.status_code == 400

    async def test_partial_uuid_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_player(x_player_id="12345678-1234-1234")

        assert exc_info.value.status_code == 400

    async def test_returns_uuid_with_correct_value(self):
        """The UUID returned has the same value as the header string."""
        raw = "123e4567-e89b-12d3-a456-426614174000"

        result = await get_current_player(x_player_id=raw)

        assert str(result) == raw
