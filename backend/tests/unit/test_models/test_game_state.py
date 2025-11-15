"""Tests for game_state model."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.character import Character, CharacterStats
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.world import WorldState, Location
from agentic_rpg.models.conversation import Conversation
from agentic_rpg.models.versioning import SchemaVersion


class TestGameState:
    """Test GameState model."""

    def test_valid_game_state(self):
        """Test creating valid game state."""
        char = Character(
            id="char_001",
            name="Test Hero",
            profession="Adventurer",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50
            ),
            location="start_location"
        )

        location = Location(
            id="start_location",
            name="Starting Village",
            description="A peaceful village",
            type="settlement"
        )

        world = WorldState(current_location=location)

        state = GameState(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            character=char,
            inventory=Inventory(),
            world=world,
            conversation=Conversation()
        )

        assert state.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert state.character.name == "Test Hero"
        assert state.inventory.items == []
        assert state.world.current_location.name == "Starting Village"
        assert state.conversation.messages == []

    def test_game_state_default_schema_version(self):
        """Test default schema_version is set."""
        char = Character(
            id="char_001",
            name="Test Hero",
            profession="Adventurer",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50
            ),
            location="start_location"
        )

        location = Location(
            id="start_location",
            name="Starting Village",
            description="A peaceful village",
            type="settlement"
        )

        state = GameState(
            session_id="test_session",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            character=char,
            inventory=Inventory(),
            world=WorldState(current_location=location),
            conversation=Conversation()
        )

        assert state.schema_version == SchemaVersion.CURRENT

    def test_game_state_json_schema_extra(self):
        """Test that JSON schema examples are defined."""
        schema = GameState.model_json_schema()
        assert "examples" in schema
        assert len(schema["examples"]) > 0

    def test_game_state_serialization(self):
        """Test game state can be serialized to JSON."""
        char = Character(
            id="char_001",
            name="Test Hero",
            profession="Adventurer",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50
            ),
            location="start_location"
        )

        location = Location(
            id="start_location",
            name="Starting Village",
            description="A peaceful village",
            type="settlement"
        )

        state = GameState(
            session_id="test_session",
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
            character=char,
            inventory=Inventory(),
            world=WorldState(current_location=location),
            conversation=Conversation()
        )

        json_data = state.model_dump()
        assert json_data["session_id"] == "test_session"
        assert json_data["character"]["name"] == "Test Hero"
        assert json_data["schema_version"] == SchemaVersion.CURRENT
