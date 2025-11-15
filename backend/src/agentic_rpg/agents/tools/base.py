"""Base tool interfaces."""
from typing import Any, Protocol


class GameTool(Protocol):
    """Interface for all game tools callable by agents."""

    name: str
    description: str
    schema: dict[str, Any]  # JSON schema for parameters

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool and return results."""
        ...

    def validate(self, **kwargs: Any) -> bool:
        """Validate tool parameters before execution."""
        ...
