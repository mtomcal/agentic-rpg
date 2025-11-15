"""Tests for world models."""
import pytest
from pydantic import ValidationError

from agentic_rpg.models.world import NPC, Location, WorldState


class TestNPC:
    """Test NPC model."""

    def test_valid_npc(self):
        """Test creating valid NPC."""
        npc = NPC(
            id="npc_001",
            name="Merchant Bob",
            description="A friendly merchant",
            personality="friendly",
            dialogue_state={"greeting_given": True}
        )
        assert npc.id == "npc_001"
        assert npc.name == "Merchant Bob"
        assert npc.description == "A friendly merchant"
        assert npc.personality == "friendly"
        assert npc.dialogue_state["greeting_given"] is True

    def test_npc_default_personality(self):
        """Test default personality is neutral."""
        npc = NPC(id="npc_001", name="Test NPC", description="A test NPC")
        assert npc.personality == "neutral"

    def test_npc_default_dialogue_state(self):
        """Test default dialogue_state is empty dict."""
        npc = NPC(id="npc_001", name="Test NPC", description="A test NPC")
        assert npc.dialogue_state == {}


class TestLocation:
    """Test Location model."""

    def test_valid_location(self):
        """Test creating valid location."""
        npc = NPC(id="npc_001", name="Guard", description="A guard")
        location = Location(
            id="loc_001",
            name="Town Square",
            description="A bustling town square with many people",
            type="city",
            connections=["loc_002", "loc_003"],
            npcs=[npc],
            properties={"safe_zone": True}
        )
        assert location.id == "loc_001"
        assert location.name == "Town Square"
        assert location.type == "city"
        assert len(location.connections) == 2
        assert len(location.npcs) == 1
        assert location.properties["safe_zone"] is True

    def test_location_default_connections(self):
        """Test default connections is empty list."""
        location = Location(
            id="loc_001",
            name="Town Square",
            description="A bustling town square",
            type="city"
        )
        assert location.connections == []

    def test_location_default_npcs(self):
        """Test default npcs is empty list."""
        location = Location(
            id="loc_001",
            name="Town Square",
            description="A bustling town square",
            type="city"
        )
        assert location.npcs == []

    def test_location_default_properties(self):
        """Test default properties is empty dict."""
        location = Location(
            id="loc_001",
            name="Town Square",
            description="A bustling town square",
            type="city"
        )
        assert location.properties == {}

    def test_location_name_min_length(self):
        """Test that name must be at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            Location(
                id="loc_001",
                name="",
                description="A bustling town square",
                type="city"
            )
        assert "name" in str(exc_info.value)

    def test_location_description_min_length(self):
        """Test that description must be at least 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Location(
                id="loc_001",
                name="Town Square",
                description="Short",
                type="city"
            )
        assert "description" in str(exc_info.value)


class TestWorldState:
    """Test WorldState model."""

    def test_valid_world_state(self):
        """Test creating valid world state."""
        current_loc = Location(
            id="loc_001",
            name="Starting Village",
            description="A peaceful starting village",
            type="settlement"
        )
        world = WorldState(
            current_location=current_loc,
            available_locations=[current_loc],
            time_of_day="day",
            weather="clear",
            discovered_locations=["loc_001"]
        )
        assert world.current_location.id == "loc_001"
        assert len(world.available_locations) == 1
        assert world.time_of_day == "day"
        assert world.weather == "clear"
        assert "loc_001" in world.discovered_locations

    def test_world_state_default_available_locations(self):
        """Test default available_locations is empty list."""
        current_loc = Location(
            id="loc_001",
            name="Starting Village",
            description="A peaceful starting village",
            type="settlement"
        )
        world = WorldState(current_location=current_loc)
        assert world.available_locations == []

    def test_world_state_default_time_of_day(self):
        """Test default time_of_day is day."""
        current_loc = Location(
            id="loc_001",
            name="Starting Village",
            description="A peaceful starting village",
            type="settlement"
        )
        world = WorldState(current_location=current_loc)
        assert world.time_of_day == "day"

    def test_world_state_default_weather(self):
        """Test default weather is clear."""
        current_loc = Location(
            id="loc_001",
            name="Starting Village",
            description="A peaceful starting village",
            type="settlement"
        )
        world = WorldState(current_location=current_loc)
        assert world.weather == "clear"

    def test_world_state_default_discovered_locations(self):
        """Test default discovered_locations is empty list."""
        current_loc = Location(
            id="loc_001",
            name="Starting Village",
            description="A peaceful starting village",
            type="settlement"
        )
        world = WorldState(current_location=current_loc)
        assert world.discovered_locations == []
