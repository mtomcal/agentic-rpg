"""Service interface definitions using Protocol."""
from typing import Protocol

from agentic_rpg.models.character import Character
from agentic_rpg.models.game_state import GameState


class StateManager(Protocol):
    """Interface for game state persistence."""

    def create_session(self, character: Character) -> str:
        """Create new game session, return session ID."""
        ...

    def load_state(self, session_id: str) -> GameState:
        """Load complete game state."""
        ...

    def update_state(self, session_id: str, updates: dict[str, object]) -> GameState:
        """Apply partial updates to state."""
        ...

    def delete_session(self, session_id: str) -> bool:
        """Delete game session."""
        ...
