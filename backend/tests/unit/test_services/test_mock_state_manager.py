"""Tests for Mock State Manager."""
from datetime import datetime

import pytest

from agentic_rpg.models.character import Character, CharacterStats
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.services.mock_state_manager import MockStateManager


class TestMockStateManager:
    """Test MockStateManager functionality."""

    @pytest.fixture
    def state_manager(self):
        """Create a fresh state manager for each test."""
        return MockStateManager()

    @pytest.fixture
    def test_character(self):
        """Create a test character."""
        return Character(
            id="char_test_123",
            name="Test Hero",
            profession="Warrior",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50,
                money=100
            ),
            location="start_location"
        )

    def test_create_session(self, state_manager, test_character):
        """Test creating a new game session."""
        session_id = state_manager.create_session(test_character)

        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_create_session_returns_unique_ids(self, state_manager, test_character):
        """Test that each session gets a unique ID."""
        session_id1 = state_manager.create_session(test_character)
        session_id2 = state_manager.create_session(test_character)

        assert session_id1 != session_id2

    def test_create_session_initializes_state(self, state_manager, test_character):
        """Test that created session has proper initial state."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert isinstance(state, GameState)
        assert state.session_id == session_id
        assert state.character.name == "Test Hero"
        assert state.character.profession == "Warrior"
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)

    def test_create_session_initializes_inventory(self, state_manager, test_character):
        """Test that created session has empty inventory."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert isinstance(state.inventory, Inventory)

    def test_create_session_initializes_world(self, state_manager, test_character):
        """Test that created session has starting location."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert state.world is not None
        assert state.world.current_location is not None
        assert state.world.current_location.name == "Starting Village"
        assert state.world.current_location.type == "settlement"

    def test_load_state(self, state_manager, test_character):
        """Test loading a game state."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert isinstance(state, GameState)
        assert state.session_id == session_id

    def test_load_nonexistent_state_raises_error(self, state_manager):
        """Test that loading nonexistent session raises error."""
        with pytest.raises(KeyError, match="not found"):
            state_manager.load_state("nonexistent_session_id")

    def test_update_state(self, state_manager, test_character):
        """Test updating game state."""
        session_id = state_manager.create_session(test_character)

        # Create a new character with different stats
        updated_character = Character(
            id="char_updated_456",
            name="Updated Hero",
            profession="Wizard",
            stats=CharacterStats(
                health=80,
                max_health=80,
                energy=100,
                max_energy=100,
                money=500
            ),
            location="wizard_tower"
        )

        updated_state = state_manager.update_state(
            session_id,
            {"character": updated_character}
        )

        assert updated_state.character.name == "Updated Hero"
        assert updated_state.character.profession == "Wizard"
        assert updated_state.character.stats.max_health == 80

    def test_update_state_updates_timestamp(self, state_manager, test_character):
        """Test that updating state updates the timestamp."""
        session_id = state_manager.create_session(test_character)
        original_state = state_manager.load_state(session_id)
        original_updated_at = original_state.updated_at

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        updated_state = state_manager.update_state(session_id, {})

        assert updated_state.updated_at > original_updated_at

    def test_update_nonexistent_state_raises_error(self, state_manager):
        """Test that updating nonexistent session raises error."""
        with pytest.raises(KeyError, match="not found"):
            state_manager.update_state("nonexistent_session_id", {})

    def test_delete_session(self, state_manager, test_character):
        """Test deleting a game session."""
        session_id = state_manager.create_session(test_character)

        # Verify session exists
        state = state_manager.load_state(session_id)
        assert state is not None

        # Delete session
        result = state_manager.delete_session(session_id)
        assert result is True

        # Verify session is gone
        with pytest.raises(KeyError):
            state_manager.load_state(session_id)

    def test_delete_nonexistent_session(self, state_manager):
        """Test deleting nonexistent session returns False."""
        result = state_manager.delete_session("nonexistent_session_id")
        assert result is False

    def test_multiple_sessions_isolated(self, state_manager, test_character):
        """Test that multiple sessions are isolated from each other."""
        # Create two sessions
        session_id1 = state_manager.create_session(test_character)
        session_id2 = state_manager.create_session(test_character)

        # Update first session
        updated_character = Character(
            id="char_updated_789",
            name="Updated Hero",
            profession="Wizard",
            stats=CharacterStats(
                health=150,
                max_health=150,
                energy=200,
                max_energy=200,
                money=5000
            ),
            location="magic_academy"
        )
        state_manager.update_state(session_id1, {"character": updated_character})

        # Verify second session unchanged
        state2 = state_manager.load_state(session_id2)
        assert state2.character.name == "Test Hero"
        assert state2.character.stats.max_health == 100

    def test_state_persistence_in_memory(self, state_manager, test_character):
        """Test that state persists in memory across operations."""
        session_id = state_manager.create_session(test_character)

        # Update state
        updated_character = Character(
            id="char_persistent_999",
            name="Persistent Hero",
            profession="Rogue",
            stats=CharacterStats(
                health=90,
                max_health=90,
                energy=70,
                max_energy=70,
                money=300
            ),
            location="thieves_guild"
        )
        state_manager.update_state(session_id, {"character": updated_character})

        # Load again and verify persistence
        state = state_manager.load_state(session_id)
        assert state.character.name == "Persistent Hero"
        assert state.character.profession == "Rogue"
        assert state.character.stats.max_health == 90

    def test_initial_conversation_state(self, state_manager, test_character):
        """Test that conversation is initialized."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert state.conversation is not None

    def test_initial_world_has_discovered_locations(self, state_manager, test_character):
        """Test that starting location is marked as discovered."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert len(state.world.discovered_locations) > 0
        assert state.world.current_location.id in state.world.discovered_locations

    def test_initial_world_has_available_locations(self, state_manager, test_character):
        """Test that starting location is in available locations."""
        session_id = state_manager.create_session(test_character)
        state = state_manager.load_state(session_id)

        assert len(state.world.available_locations) > 0
        assert any(
            loc.id == state.world.current_location.id
            for loc in state.world.available_locations
        )
