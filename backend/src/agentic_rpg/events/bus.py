"""In-process async event bus for game events."""

import asyncio
import logging
from collections import defaultdict, deque
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from agentic_rpg.models.events import GameEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Async publish/subscribe event bus.

    Maintains per-type subscriber lists and a bounded in-memory event history.
    """

    def __init__(self, history_limit: int = 1000) -> None:
        self._subscribers: dict[str, dict[str, Callable[[GameEvent], Awaitable[None]]]] = defaultdict(dict)
        self._sub_id_to_type: dict[str, str] = {}
        self._history: deque[GameEvent] = deque(maxlen=history_limit)

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[GameEvent], Awaitable[None]],
    ) -> str:
        """Register an async callback for a specific event type.

        Returns a unique subscription ID that can be used to unsubscribe.
        """
        sub_id = str(uuid4())
        self._subscribers[event_type][sub_id] = callback
        self._sub_id_to_type[sub_id] = event_type
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by ID. No-op if the ID is unknown."""
        event_type = self._sub_id_to_type.pop(subscription_id, None)
        if event_type is not None:
            self._subscribers[event_type].pop(subscription_id, None)

    async def publish(self, event: GameEvent) -> None:
        """Emit an event to all subscribers of that event type.

        Subscribers are invoked concurrently. Errors in subscribers are logged
        but do not block other subscribers or the publisher.
        The event is always stored in history regardless of subscriber errors.
        """
        self._history.append(event)

        callbacks = list(self._subscribers.get(event.event_type, {}).values())
        if not callbacks:
            return

        tasks = [callback(event) for callback in callbacks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(
                    "Subscriber error for event %s: %s",
                    event.event_type,
                    result,
                )

    def publish_sync(self, event: GameEvent) -> None:
        """Synchronous event publish for use in sync tool contexts.

        Appends to history and invokes subscriber coroutines by driving them
        to completion inline. Works for simple callbacks that don't truly
        suspend (e.g. callbacks that just append to a list).
        """
        self._history.append(event)

        callbacks = list(self._subscribers.get(event.event_type, {}).values())
        for callback in callbacks:
            coro = callback(event)
            try:
                coro.send(None)
            except StopIteration:
                pass

    async def get_history(
        self,
        event_type: str | None = None,
        session_id: UUID | None = None,
        limit: int = 100,
    ) -> list[GameEvent]:
        """Retrieve events from history with optional filtering.

        Args:
            event_type: Filter by event type string.
            session_id: Filter by session UUID.
            limit: Maximum number of events to return.

        Returns:
            List of matching events in insertion order.
        """
        events: list[GameEvent] = []
        for event in self._history:
            if event_type is not None and event.event_type != event_type:
                continue
            if session_id is not None and event.session_id != session_id:
                continue
            events.append(event)
            if len(events) >= limit:
                break
        return events
