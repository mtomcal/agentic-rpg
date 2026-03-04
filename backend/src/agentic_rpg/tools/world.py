"""World tools — inspect and modify world/location state."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.events import GameEvent
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.world import Location


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------
class MoveCharacterInput(BaseModel):
    """Input for move_character."""

    location_id: str = Field(description="ID of the location to move to")


class InspectEnvironmentInput(BaseModel):
    """Input for inspect_environment."""

    focus: str | None = Field(default=None, description="Optional focus element to examine")


class AddLocationInput(BaseModel):
    """Input for add_location."""

    location_id: str = Field(description="Unique identifier for the new location")
    name: str = Field(description="Display name of the location")
    description: str = Field(default="", description="Location description text")
    connections: list[str] = Field(default_factory=list, description="IDs of connected locations")


class SetWorldFlagInput(BaseModel):
    """Input for set_world_flag."""

    key: str = Field(description="Flag key name")
    value: Any = Field(description="Flag value")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _emit(event_bus: EventBus, game_state: GameState, event_type: str, payload: dict) -> None:
    """Publish an event synchronously via the event bus."""
    event = GameEvent(
        event_type=event_type,
        payload=payload,
        source="tool:world",
        session_id=game_state.session.session_id,
    )
    event_bus.publish_sync(event)


# ---------------------------------------------------------------------------
# GetCurrentLocationTool
# ---------------------------------------------------------------------------
class GetCurrentLocationTool(BaseTool):
    """Get details of the character's current location."""

    name: str = "get_current_location"
    description: str = "Get current location details including connections and NPCs."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        loc = self.game_state.world.locations.get(self.game_state.world.current_location_id)
        if loc is None:
            return {"id": self.game_state.world.current_location_id, "name": self.game_state.world.current_location_id, "description": "Unknown location", "connections": []}
        return loc.model_dump()


# ---------------------------------------------------------------------------
# GetConnectionsTool
# ---------------------------------------------------------------------------
class GetConnectionsTool(BaseTool):
    """List locations connected to the current location."""

    name: str = "get_connections"
    description: str = "List all locations connected to the current location."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        current = self.game_state.world.locations.get(self.game_state.world.current_location_id)
        if current is None:
            return {"connections": []}
        connections = []
        for conn_id in current.connections:
            if conn_id in self.game_state.world.locations:
                loc = self.game_state.world.locations[conn_id]
                connections.append({"id": loc.id, "name": loc.name, "visited": loc.visited})
            else:
                connections.append({"id": conn_id, "name": conn_id, "visited": False})
        return {"connections": connections}


# ---------------------------------------------------------------------------
# MoveCharacterTool
# ---------------------------------------------------------------------------
class MoveCharacterTool(BaseTool):
    """Move the character to a connected location."""

    name: str = "move_character"
    description: str = "Move the character to a connected location."
    args_schema: type = MoveCharacterInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, location_id: str) -> dict:
        world = self.game_state.world
        current = world.locations.get(world.current_location_id)

        if current is None:
            return {"success": False, "error": "Current location not found"}

        if location_id not in current.connections:
            return {"success": False, "error": f"'{location_id}' is not connected to current location"}

        if location_id not in world.locations:
            return {"success": False, "error": f"Location '{location_id}' does not exist"}

        from_location = world.current_location_id
        world.current_location_id = location_id
        self.game_state.character.location_id = location_id
        world.locations[location_id].visited = True
        world.discovered_locations.add(location_id)

        _emit(self.event_bus, self.game_state, "world.character_moved", {
            "from_location": from_location,
            "to_location": location_id,
        })

        return {"success": True, "location_id": location_id}


# ---------------------------------------------------------------------------
# InspectEnvironmentTool
# ---------------------------------------------------------------------------
class InspectEnvironmentTool(BaseTool):
    """Get a detailed description of the current location."""

    name: str = "inspect_environment"
    description: str = "Get detailed location description, optionally focusing on a specific element."
    args_schema: type = InspectEnvironmentInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, focus: str | None = None) -> dict:
        loc = self.game_state.world.locations.get(self.game_state.world.current_location_id)
        if loc is None:
            return {"id": self.game_state.world.current_location_id, "name": self.game_state.world.current_location_id, "description": "Unknown location", "focus": focus}
        result = loc.model_dump()
        result["focus"] = focus
        return result


# ---------------------------------------------------------------------------
# AddLocationTool
# ---------------------------------------------------------------------------
class AddLocationTool(BaseTool):
    """Create a new location in the game world."""

    name: str = "add_location"
    description: str = "Create a new location in the world."
    args_schema: type = AddLocationInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, location_id: str, name: str, description: str = "", connections: list[str] | None = None) -> dict:
        if connections is None:
            connections = []

        if location_id in self.game_state.world.locations:
            return {"success": False, "error": f"Location '{location_id}' already exists"}

        new_location = Location(
            id=location_id,
            name=name,
            description=description,
            connections=connections,
        )
        self.game_state.world.locations[location_id] = new_location

        _emit(self.event_bus, self.game_state, "world.location_added", {
            "location_id": location_id,
            "name": name,
        })

        return {"success": True, "location_id": location_id, "name": name}


# ---------------------------------------------------------------------------
# SetWorldFlagTool
# ---------------------------------------------------------------------------
class SetWorldFlagTool(BaseTool):
    """Set a world state flag."""

    name: str = "set_world_flag"
    description: str = "Set a key-value flag in world state."
    args_schema: type = SetWorldFlagInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, key: str, value: Any) -> dict:
        old_value = self.game_state.world.world_flags.get(key)
        self.game_state.world.world_flags[key] = value

        _emit(self.event_bus, self.game_state, "world.flag_set", {
            "key": key,
            "value": value,
            "old_value": old_value,
        })

        return {"success": True, "key": key, "value": value}
