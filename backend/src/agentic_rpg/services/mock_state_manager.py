"""Mock state manager for testing."""
import uuid
from datetime import UTC, datetime

from agentic_rpg.models.character import Character
from agentic_rpg.models.conversation import Conversation
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.world import Location, WorldState


class MockStateManager:
    """In-memory state manager for testing."""

    def __init__(self) -> None:
        self._sessions: dict[str, GameState] = {}

    def create_session(self, character: Character) -> str:
        """Create new game session."""
        session_id = str(uuid.uuid4())

        # Create initial location
        start_location = Location(
            id="start_location",
            name="Starting Village",
            description="A peaceful village where your journey begins",
            type="settlement",
            connections=[],
            npcs=[],
            properties={}
        )

        # Create initial game state
        state = GameState(
            session_id=session_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            character=character,
            inventory=Inventory(),
            world=WorldState(
                current_location=start_location,
                available_locations=[start_location],
                discovered_locations=[start_location.id]
            ),
            conversation=Conversation()
        )

        self._sessions[session_id] = state
        return session_id

    def load_state(self, session_id: str) -> GameState:
        """Load game state."""
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def update_state(self, session_id: str, updates: dict[str, object]) -> GameState:
        """Apply updates to state."""
        state = self.load_state(session_id)

        # Simple deep update (extend for nested updates)
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)

        state.updated_at = datetime.now(UTC)
        return state

    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
