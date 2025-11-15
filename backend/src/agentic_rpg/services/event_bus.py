"""Event bus for component communication."""
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types."""
    STATE_UPDATED = "state.updated"
    GAME_CREATED = "game.created"
    ITEM_ACQUIRED = "inventory.item_acquired"
    LOCATION_CHANGED = "world.location_changed"


@dataclass
class EventSchema:
    """Schema definition for event validation."""
    type: str
    required_fields: set[str]
    optional_fields: set[str] = field(default_factory=set)

    def validate(self, payload: dict[str, object]) -> tuple[bool, str]:
        """Validate event payload against schema."""
        missing = self.required_fields - set(payload.keys())
        if missing:
            return False, f"Missing required fields: {missing}"

        extra = set(payload.keys()) - (self.required_fields | self.optional_fields)
        if extra:
            return False, f"Unexpected fields: {extra}"

        return True, ""


@dataclass
class GameEvent:
    """Game event with validated payload."""
    type: str
    payload: dict[str, object]
    source: str  # Component that triggered event
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    session_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class EventBus:
    """Central event bus for component communication."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[GameEvent], None]]] = {}
        self._schemas: dict[str, EventSchema] = {}
        self._history: deque[GameEvent] = deque(maxlen=1000)
        self._max_history = 1000

    def register_schema(self, schema: EventSchema) -> None:
        """Register event schema for validation."""
        self._schemas[schema.type] = schema

    def publish(self, event: GameEvent) -> None:
        """Publish event to all subscribers."""
        # Validate if schema exists
        if event.type in self._schemas:
            valid, error = self._schemas[event.type].validate(event.payload)
            if not valid:
                raise ValueError(f"Invalid event payload: {error}")

        # Store in history (deque automatically handles max size)
        self._history.append(event)

        # Notify subscribers
        subscribers = self._subscribers.get(event.type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                # Log but don't fail
                logger.exception("Error in event subscriber for event type %s: %s", event.type, e)

    def subscribe(self, event_type: str, callback: Callable[[GameEvent], None]) -> None:
        """Subscribe to specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[GameEvent], None]) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def get_history(
        self,
        event_type: str | None = None,
        session_id: str | None = None,
        limit: int = 100
    ) -> list[GameEvent]:
        """Get event history for debugging/replay."""
        events = list(self._history)

        if event_type:
            events = [e for e in events if e.type == event_type]

        if session_id:
            events = [e for e in events if e.session_id == session_id]

        return events[-limit:]


# Global event bus instance
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    return _event_bus
