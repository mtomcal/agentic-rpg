"""Schema version management and migrations."""
from collections.abc import Callable
from typing import Any


class SchemaVersion:
    """Schema version management and migrations."""

    CURRENT = "1.0.0"
    MINIMUM_COMPATIBLE = "1.0.0"

    _migrations: dict[tuple[str, str], Callable[[dict[str, Any]], dict[str, Any]]] = {}

    @classmethod
    def register_migration(cls, from_version: str, to_version: str) -> Callable[[Callable[[dict[str, Any]], dict[str, Any]]], Callable[[dict[str, Any]], dict[str, Any]]]:
        """Decorator to register schema migrations."""
        def decorator(func: Callable[[dict[str, Any]], dict[str, Any]]) -> Callable[[dict[str, Any]], dict[str, Any]]:
            cls._migrations[(from_version, to_version)] = func
            return func
        return decorator

    @classmethod
    def migrate(cls, state: dict[str, Any], from_version: str, to_version: str) -> dict[str, Any]:
        """Apply migrations to bring state to target version."""
        # Simple implementation for now - extend as needed
        if from_version == to_version:
            return state

        # Will implement migration logic in future phases
        state["schema_version"] = to_version
        return state
