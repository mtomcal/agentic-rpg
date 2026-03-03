"""Event payload registry — maps event types to Pydantic payload models."""

from typing import Type

from agentic_rpg.models.events import EventPayload


class EventPayloadRegistry:
    """Registry mapping event type strings to their Pydantic payload models.

    Provides registration (via explicit call or decorator), validation,
    and discovery of event payload schemas.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Type[EventPayload]] = {}

    def register(self, event_type: str, model: Type[EventPayload]) -> None:
        """Register a Pydantic payload model for an event type."""
        self._registry[event_type] = model

    def payload_for(self, event_type: str) -> Type[EventPayload] | None:
        """Look up the payload model for an event type, or None if unregistered."""
        return self._registry.get(event_type)

    def validate_payload(self, event_type: str, payload: dict) -> EventPayload:
        """Validate a payload dict against the registered model for the event type.

        Raises:
            KeyError: If no model is registered for the event type.
            ValidationError: If the payload doesn't match the model schema.
        """
        model = self._registry.get(event_type)
        if model is None:
            raise KeyError(f"No payload model registered for event type: {event_type}")
        return model(**payload)

    def registered_types(self) -> list[str]:
        """Return all registered event type strings."""
        return list(self._registry.keys())

    def is_registered(self, event_type: str) -> bool:
        """Check if an event type has a registered payload model."""
        return event_type in self._registry
