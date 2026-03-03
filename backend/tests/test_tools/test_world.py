"""Tests for world tools — get_current_location, get_connections, move_character,
inspect_environment, add_location, set_world_flag."""

import asyncio

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.world import Location
from agentic_rpg.tools.world import (
    AddLocationTool,
    GetConnectionsTool,
    GetCurrentLocationTool,
    InspectEnvironmentTool,
    MoveCharacterTool,
    SetWorldFlagTool,
)


# ---------------------------------------------------------------------------
# Helper to build tool with injected deps
# ---------------------------------------------------------------------------
def _make(cls, game_state: GameState, event_bus: EventBus):
    return cls(game_state=game_state, event_bus=event_bus)


# ===========================================================================
# GetCurrentLocationTool
# ===========================================================================
class TestGetCurrentLocationTool:
    def test_returns_current_location(self, tool_game_state, tool_event_bus):
        tool = _make(GetCurrentLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["id"] == "tavern"
        assert result["name"] == "The Rusty Flagon"
        assert result["description"] == "A dimly lit tavern smelling of ale"

    def test_includes_connections(self, tool_game_state, tool_event_bus):
        tool = _make(GetCurrentLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert set(result["connections"]) == {"market", "alley"}

    def test_includes_npcs(self, tool_game_state, tool_event_bus):
        tool = _make(GetCurrentLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["npcs_present"] == ["bartender"]

    def test_includes_visited_flag(self, tool_game_state, tool_event_bus):
        tool = _make(GetCurrentLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["visited"] is True


# ===========================================================================
# GetConnectionsTool
# ===========================================================================
class TestGetConnectionsTool:
    def test_returns_connected_locations(self, tool_game_state, tool_event_bus):
        tool = _make(GetConnectionsTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        names = [loc["name"] for loc in result["connections"]]
        assert "Market Square" in names
        assert "Dark Alley" in names
        assert len(result["connections"]) == 2

    def test_each_connection_has_correct_id_and_name(self, tool_game_state, tool_event_bus):
        tool = _make(GetConnectionsTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        conn_map = {c["id"]: c["name"] for c in result["connections"]}
        assert conn_map["market"] == "Market Square"
        assert conn_map["alley"] == "Dark Alley"

    def test_each_connection_includes_visited_flag(self, tool_game_state, tool_event_bus):
        tool = _make(GetConnectionsTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        conn_map = {c["id"]: c["visited"] for c in result["connections"]}
        assert conn_map["market"] is True
        assert conn_map["alley"] is False

    def test_single_connection_returns_one(self, tool_game_state, tool_event_bus):
        # alley only connects to tavern
        tool_game_state.world.current_location_id = "alley"
        tool = _make(GetConnectionsTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert len(result["connections"]) == 1
        assert result["connections"][0]["id"] == "tavern"
        assert result["connections"][0]["name"] == "The Rusty Flagon"

    def test_connection_to_unknown_location_uses_id_as_name(self, tool_game_state, tool_event_bus):
        """Covers line 98: connection ID not in locations dict falls back to id as name."""
        # Add a connection to a location that doesn't exist in the locations dict
        tool_game_state.world.locations["tavern"].connections.append("unknown_place")
        tool = _make(GetConnectionsTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        unknown_conns = [c for c in result["connections"] if c["id"] == "unknown_place"]
        assert len(unknown_conns) == 1
        assert unknown_conns[0]["name"] == "unknown_place"
        assert unknown_conns[0]["visited"] is False


# ===========================================================================
# MoveCharacterTool
# ===========================================================================
class TestMoveCharacterTool:
    def test_move_to_connected_location(self, tool_game_state, tool_event_bus):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"location_id": "market"})
        assert result["success"] is True
        assert result["location_id"] == "market"
        assert tool_game_state.world.current_location_id == "market"
        assert tool_game_state.character.location_id == "market"

    def test_move_marks_location_visited(self, tool_game_state, tool_event_bus):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        assert tool_game_state.world.locations["alley"].visited is False
        result = tool.invoke({"location_id": "alley"})
        assert result["success"] is True
        assert tool_game_state.world.locations["alley"].visited is True

    def test_move_adds_to_discovered(self, tool_game_state, tool_event_bus):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        assert "alley" not in tool_game_state.world.discovered_locations
        tool.invoke({"location_id": "alley"})
        assert "alley" in tool_game_state.world.discovered_locations

    def test_move_to_unconnected_location_fails(self, tool_game_state, tool_event_bus):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"location_id": "gate"})
        assert result["success"] is False
        assert result["error"] == "'gate' is not connected to current location"
        # State should not change
        assert tool_game_state.world.current_location_id == "tavern"

    def test_move_to_nonexistent_location_fails(self, tool_game_state, tool_event_bus):
        """Location is listed in connections but doesn't exist in locations dict.
        Covers line 126."""
        # Add 'void' to connections so it passes the connection check but fails existence check
        tool_game_state.world.locations["tavern"].connections.append("void")
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"location_id": "void"})
        assert result["success"] is False
        assert result["error"] == "Location 'void' does not exist"
        # State should not change
        assert tool_game_state.world.current_location_id == "tavern"

    def test_move_when_current_location_not_found(self, tool_game_state, tool_event_bus):
        """Covers line 120: current_location_id points to a location not in the dict."""
        tool_game_state.world.current_location_id = "deleted_location"
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"location_id": "market"})
        assert result["success"] is False
        assert result["error"] == "Current location not found"

    async def test_emits_character_moved_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        tool.invoke({"location_id": "market"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "world.character_moved"
        assert evt.payload["from_location"] == "tavern"
        assert evt.payload["to_location"] == "market"
        assert evt.source == "tool:world"

    async def test_no_event_on_failed_move(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        tool.invoke({"location_id": "gate"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0

    async def test_no_event_when_current_location_missing(self, tool_game_state, tool_event_bus, emitted_events):
        """No event when current location is not found."""
        tool_game_state.world.current_location_id = "deleted_location"
        tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        tool.invoke({"location_id": "market"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# InspectEnvironmentTool
# ===========================================================================
class TestInspectEnvironmentTool:
    def test_inspect_returns_full_location(self, tool_game_state, tool_event_bus):
        tool = _make(InspectEnvironmentTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["name"] == "The Rusty Flagon"
        assert result["description"] == "A dimly lit tavern smelling of ale"
        assert set(result["connections"]) == {"market", "alley"}
        assert result["npcs_present"] == ["bartender"]
        assert result["items_present"] == []

    def test_inspect_with_focus(self, tool_game_state, tool_event_bus):
        tool = _make(InspectEnvironmentTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"focus": "bartender"})
        assert result["name"] == "The Rusty Flagon"
        assert result["focus"] == "bartender"

    def test_inspect_without_focus(self, tool_game_state, tool_event_bus):
        tool = _make(InspectEnvironmentTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["focus"] is None

    def test_inspect_includes_id(self, tool_game_state, tool_event_bus):
        tool = _make(InspectEnvironmentTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["id"] == "tavern"

    def test_inspect_after_move_reflects_new_location(self, tool_game_state, tool_event_bus):
        """Inspect should reflect the current location after a move."""
        move_tool = _make(MoveCharacterTool, tool_game_state, tool_event_bus)
        move_tool.invoke({"location_id": "market"})
        inspect_tool = _make(InspectEnvironmentTool, tool_game_state, tool_event_bus)
        result = inspect_tool.invoke({})
        assert result["name"] == "Market Square"
        assert result["description"] == "A bustling marketplace"


# ===========================================================================
# AddLocationTool
# ===========================================================================
class TestAddLocationTool:
    def test_add_new_location(self, tool_game_state, tool_event_bus):
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "location_id": "dungeon",
            "name": "Dark Dungeon",
            "description": "A damp underground passage",
            "connections": ["alley"],
        })
        assert result["success"] is True
        assert result["location_id"] == "dungeon"
        assert result["name"] == "Dark Dungeon"
        assert "dungeon" in tool_game_state.world.locations
        loc = tool_game_state.world.locations["dungeon"]
        assert loc.name == "Dark Dungeon"
        assert loc.description == "A damp underground passage"
        assert loc.connections == ["alley"]

    def test_add_duplicate_location_fails(self, tool_game_state, tool_event_bus):
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "location_id": "tavern",
            "name": "Another Tavern",
            "description": "Duplicate",
        })
        assert result["success"] is False
        assert result["error"] == "Location 'tavern' already exists"

    def test_add_location_with_defaults(self, tool_game_state, tool_event_bus):
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "location_id": "cave",
            "name": "Hidden Cave",
        })
        assert result["success"] is True
        loc = tool_game_state.world.locations["cave"]
        assert loc.connections == []
        assert loc.npcs_present == []
        assert loc.description == ""
        assert loc.visited is False

    def test_add_location_with_explicit_none_connections(self, tool_game_state, tool_event_bus):
        """Covers line 177: connections=None branch in _run."""
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        # Directly invoke _run with connections=None to hit the branch
        result = tool._run(location_id="void_room", name="Void Room", description="Empty", connections=None)
        assert result["success"] is True
        loc = tool_game_state.world.locations["void_room"]
        assert loc.connections == []

    async def test_emits_location_added_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        tool.invoke({
            "location_id": "dungeon",
            "name": "Dark Dungeon",
            "description": "A dark place",
        })
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "world.location_added"
        assert evt.payload["location_id"] == "dungeon"
        assert evt.payload["name"] == "Dark Dungeon"
        assert evt.source == "tool:world"

    async def test_no_event_on_duplicate_location(self, tool_game_state, tool_event_bus, emitted_events):
        """No event should be emitted when adding a duplicate location."""
        tool = _make(AddLocationTool, tool_game_state, tool_event_bus)
        tool.invoke({
            "location_id": "tavern",
            "name": "Duplicate",
            "description": "Duplicate",
        })
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# SetWorldFlagTool
# ===========================================================================
class TestSetWorldFlagTool:
    def test_set_new_flag(self, tool_game_state, tool_event_bus):
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"key": "dragon_slain", "value": True})
        assert result["success"] is True
        assert result["key"] == "dragon_slain"
        assert result["value"] is True
        assert tool_game_state.world.world_flags["dragon_slain"] is True

    def test_overwrite_existing_flag(self, tool_game_state, tool_event_bus):
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        assert tool_game_state.world.world_flags["quest_started"] is True
        result = tool.invoke({"key": "quest_started", "value": False})
        assert result["success"] is True
        assert tool_game_state.world.world_flags["quest_started"] is False

    def test_set_flag_with_string_value(self, tool_game_state, tool_event_bus):
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"key": "current_quest", "value": "find_crown"})
        assert result["success"] is True
        assert tool_game_state.world.world_flags["current_quest"] == "find_crown"

    def test_set_flag_with_numeric_value(self, tool_game_state, tool_event_bus):
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"key": "enemies_defeated", "value": 5})
        assert result["success"] is True
        assert tool_game_state.world.world_flags["enemies_defeated"] == 5

    async def test_emits_flag_set_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        tool.invoke({"key": "dragon_slain", "value": True})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "world.flag_set"
        assert evt.payload["key"] == "dragon_slain"
        assert evt.payload["value"] is True
        assert evt.source == "tool:world"

    async def test_emits_old_value_in_event(self, tool_game_state, tool_event_bus, emitted_events):
        """Event payload should include old_value when overwriting."""
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        tool.invoke({"key": "quest_started", "value": False})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.payload["old_value"] is True
        assert evt.payload["value"] is False

    async def test_emits_none_old_value_for_new_flag(self, tool_game_state, tool_event_bus, emitted_events):
        """Event payload old_value should be None when setting a brand new flag."""
        tool = _make(SetWorldFlagTool, tool_game_state, tool_event_bus)
        tool.invoke({"key": "new_flag", "value": "hello"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.payload["old_value"] is None
        assert evt.payload["value"] == "hello"
