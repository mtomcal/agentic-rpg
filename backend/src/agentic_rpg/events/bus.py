"""In-process async event bus for game events."""

from collections import defaultdict, deque
from uuid import UUID, uuid4

from agentic_rpg.models.events import GameEvent


class EventBus:
    """Async publish/subscribe event bus.

    Maintains per-type subscriber lists and a bounded in-memory event history.
    Full implementation in Phase 2, item 16.
    """

    def __init__(self, history_limit: int = 1000) -> None:
        self._subscribers: dict[str, dict[UUID, object]] = defaultdict(dict)
        self._history: deque[GameEvent] = deque(maxlen=history_limit)
