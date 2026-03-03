"""Tests for the StateManager — CRUD operations on game sessions.

RED phase: These tests define the expected behavior of StateManager.
"""

from uuid import uuid4

import asyncpg
import pytest

from agentic_rpg.models.game_state import GameState, SessionStatus
from agentic_rpg.state.manager import StateManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def manager(clean_db):
    """Create a StateManager backed by the test DB pool."""
    return StateManager(pool=clean_db)


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for StateManager.create_session."""

    async def test_create_session_returns_game_state(self, manager, sample_game_state):
        """Creating a session should return a persisted GameState."""
        result = await manager.create_session(sample_game_state)
        assert isinstance(result, GameState)
        assert result.session.session_id == sample_game_state.session.session_id

    async def test_create_session_persists_to_db(self, manager, sample_game_state):
        """After creation, the session should be loadable from DB."""
        await manager.create_session(sample_game_state)
        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        assert loaded.session.session_id == sample_game_state.session.session_id
        assert loaded.character.name == "Aldric"
        assert loaded.character.stats["health"] == 80.0

    async def test_create_session_sets_player_row(self, manager, sample_game_state, clean_db):
        """Creating a session should also create the player row if needed."""
        await manager.create_session(sample_game_state)
        row = await clean_db.fetchrow(
            "SELECT id FROM players WHERE id = $1",
            sample_game_state.session.player_id,
        )
        assert row is not None
        assert row["id"] == sample_game_state.session.player_id

    async def test_create_duplicate_session_raises(self, manager, sample_game_state):
        """Creating a session with the same ID twice should raise an error."""
        await manager.create_session(sample_game_state)
        with pytest.raises(asyncpg.UniqueViolationError):
            await manager.create_session(sample_game_state)


# ---------------------------------------------------------------------------
# load_game_state
# ---------------------------------------------------------------------------


class TestLoadGameState:
    """Tests for StateManager.load_game_state."""

    async def test_load_existing_session(self, manager, sample_game_state):
        """Loading an existing session should return the correct GameState."""
        await manager.create_session(sample_game_state)
        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        assert loaded.session.session_id == sample_game_state.session.session_id
        assert loaded.character.name == "Aldric"
        assert loaded.character.profession == "Warrior"
        assert loaded.inventory.items[0].name == "Iron Sword"
        assert loaded.world.current_location_id == "tavern"
        assert loaded.story.active_beat_index == 1
        assert len(loaded.conversation.history) == 3

    async def test_load_nonexistent_session_returns_none(self, manager):
        """Loading a session that doesn't exist should return None."""
        result = await manager.load_game_state(uuid4())
        assert result is None

    async def test_load_preserves_full_state_fidelity(self, manager, sample_game_state):
        """The loaded state should be equal to what was saved (round-trip)."""
        await manager.create_session(sample_game_state)
        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        # Check deep fields survive the JSON round-trip
        assert loaded.character.status_effects[0].name == "Blessed"
        assert loaded.character.status_effects[0].magnitude == 1.5
        assert loaded.inventory.items[1].properties["heal_amount"] == 25
        assert loaded.world.locations["tavern"].connections == ["market", "alley"]
        assert loaded.story.outline.premise == "A warrior seeks the lost crown of the Northern Kingdom"


# ---------------------------------------------------------------------------
# save_game_state
# ---------------------------------------------------------------------------


class TestSaveGameState:
    """Tests for StateManager.save_game_state."""

    async def test_save_updates_existing_session(self, manager, sample_game_state):
        """Saving should update the game state in the DB."""
        await manager.create_session(sample_game_state)

        # Mutate the state
        sample_game_state.character.stats["health"] = 50.0
        sample_game_state.character.level = 3
        await manager.save_game_state(sample_game_state)

        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        assert loaded.character.stats["health"] == 50.0
        assert loaded.character.level == 3

    async def test_save_updates_updated_at_timestamp(self, manager, sample_game_state):
        """Saving should bump the updated_at timestamp."""
        await manager.create_session(sample_game_state)
        original_updated_at = sample_game_state.session.updated_at

        sample_game_state.character.stats["health"] = 10.0
        await manager.save_game_state(sample_game_state)

        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        assert loaded.session.updated_at > original_updated_at

    async def test_save_nonexistent_session_raises(self, manager, sample_game_state):
        """Saving a session that doesn't exist should raise a ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await manager.save_game_state(sample_game_state)


# ---------------------------------------------------------------------------
# delete_game_state
# ---------------------------------------------------------------------------


class TestDeleteGameState:
    """Tests for StateManager.delete_game_state."""

    async def test_delete_removes_session(self, manager, sample_game_state):
        """Deleting a session should remove it from the DB."""
        await manager.create_session(sample_game_state)
        await manager.delete_game_state(sample_game_state.session.session_id)

        result = await manager.load_game_state(sample_game_state.session.session_id)
        assert result is None

    async def test_delete_nonexistent_session_is_noop(self, manager):
        """Deleting a session that doesn't exist should not raise and return False."""
        result = await manager.delete_game_state(uuid4())
        assert result is False

    async def test_delete_returns_true_for_existing(self, manager, sample_game_state):
        """Deleting an existing session should return True."""
        await manager.create_session(sample_game_state)
        result = await manager.delete_game_state(sample_game_state.session.session_id)
        assert result is True

    async def test_delete_returns_false_for_nonexistent(self, manager):
        """Deleting a nonexistent session should return False."""
        result = await manager.delete_game_state(uuid4())
        assert result is False


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    """Tests for StateManager.list_sessions."""

    async def test_list_sessions_empty(self, manager):
        """Listing sessions for a player with none should return empty list."""
        result = await manager.list_sessions(uuid4())
        assert result == []

    async def test_list_sessions_returns_player_sessions(
        self, manager, sample_game_state
    ):
        """Listing sessions should return all sessions for the given player."""
        await manager.create_session(sample_game_state)
        result = await manager.list_sessions(sample_game_state.session.player_id)
        assert len(result) == 1
        assert result[0].session.session_id == sample_game_state.session.session_id

    async def test_list_sessions_filters_by_player(
        self, manager, sample_game_state
    ):
        """Sessions belonging to other players should not be returned."""
        await manager.create_session(sample_game_state)

        other_player_id = uuid4()
        result = await manager.list_sessions(other_player_id)
        assert result == []

    async def test_list_sessions_returns_multiple(
        self, manager, sample_game_state, sample_player_id
    ):
        """Should return multiple sessions for the same player."""
        await manager.create_session(sample_game_state)

        # Create a second session for the same player
        second_state = sample_game_state.model_copy(deep=True)
        second_state.session.session_id = uuid4()
        await manager.create_session(second_state)

        result = await manager.list_sessions(sample_player_id)
        assert len(result) == 2
        session_ids = {s.session.session_id for s in result}
        assert sample_game_state.session.session_id in session_ids
        assert second_state.session.session_id in session_ids


# ---------------------------------------------------------------------------
# update_session_status
# ---------------------------------------------------------------------------


class TestUpdateSessionStatus:
    """Tests for StateManager.update_session_status."""

    async def test_update_status(self, manager, sample_game_state):
        """Updating status should persist the change."""
        await manager.create_session(sample_game_state)
        await manager.update_session_status(
            sample_game_state.session.session_id, SessionStatus.paused
        )
        loaded = await manager.load_game_state(sample_game_state.session.session_id)
        assert loaded.session.status == SessionStatus.paused

    async def test_update_status_nonexistent_raises(self, manager):
        """Updating status of a nonexistent session should raise a ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await manager.update_session_status(uuid4(), SessionStatus.completed)
