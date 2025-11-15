"""Main game state model."""
from pydantic import BaseModel, Field
from datetime import datetime
from .character import Character
from .inventory import Inventory
from .world import WorldState
from .conversation import Conversation
from .versioning import SchemaVersion


class GameState(BaseModel):
    """Complete game state - versioned and validated."""

    schema_version: str = Field(
        default=SchemaVersion.CURRENT,
        description="Schema version for migrations"
    )
    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    character: Character
    inventory: Inventory
    world: WorldState
    conversation: Conversation

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "schema_version": "1.0.0",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z",
                "character": {
                    "id": "char_001",
                    "name": "Test Hero",
                    "profession": "Adventurer",
                    "stats": {
                        "health": 100,
                        "max_health": 100,
                        "energy": 50,
                        "max_energy": 50,
                        "money": 1000
                    },
                    "location": "start_location",
                    "status": []
                },
                "inventory": {"items": [], "capacity": 20, "max_weight": 100.0},
                "world": {
                    "current_location": {
                        "id": "start_location",
                        "name": "Starting Village",
                        "description": "A peaceful village",
                        "type": "settlement",
                        "connections": [],
                        "npcs": [],
                        "properties": {}
                    },
                    "available_locations": [],
                    "time_of_day": "day",
                    "weather": "clear",
                    "discovered_locations": ["start_location"]
                },
                "conversation": {"messages": [], "context": [], "max_history": 100}
            }]
        }
    }
