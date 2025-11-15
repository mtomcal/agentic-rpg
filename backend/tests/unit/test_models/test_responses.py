"""Tests for API response models."""
from datetime import datetime

from agentic_rpg.models.character import Character, CharacterStats
from agentic_rpg.models.conversation import Conversation
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.responses import CreateGameResponse, GameResponse
from agentic_rpg.models.world import Location, WorldState


class TestCreateGameResponse:
    """Test CreateGameResponse model."""

    def test_valid_create_game_response(self):
        """Test creating valid create game response."""
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

        response = CreateGameResponse(
            session_id="test_session",
            state=state
        )

        assert response.session_id == "test_session"
        assert response.state.character.name == "Test Hero"


class TestGameResponse:
    """Test GameResponse model."""

    def test_valid_game_response(self):
        """Test creating valid game response."""
        response = GameResponse(
            response="You enter the tavern and see a friendly merchant.",
            state_updates={"character": {"location": "tavern"}},
            tool_calls=["move_to_location"]
        )

        assert response.response == "You enter the tavern and see a friendly merchant."
        assert response.state_updates["character"]["location"] == "tavern"
        assert "move_to_location" in response.tool_calls

    def test_game_response_default_state_updates(self):
        """Test default state_updates is empty dict."""
        response = GameResponse(response="Test response")
        assert response.state_updates == {}

    def test_game_response_default_tool_calls(self):
        """Test default tool_calls is empty list."""
        response = GameResponse(response="Test response")
        assert response.tool_calls == []

    def test_game_response_serialization(self):
        """Test game response can be serialized to JSON."""
        response = GameResponse(
            response="Test narrative",
            state_updates={"test": "value"},
            tool_calls=["tool1", "tool2"]
        )

        json_data = response.model_dump()
        assert json_data["response"] == "Test narrative"
        assert json_data["state_updates"]["test"] == "value"
        assert len(json_data["tool_calls"]) == 2
