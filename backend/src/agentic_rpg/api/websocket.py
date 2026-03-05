"""WebSocket endpoint and ConnectionHub for real-time game communication."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from agentic_rpg.agent.context import assemble_context
from agentic_rpg.agent.graph import build_agent_graph
from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.api import PlayerActionData
from agentic_rpg.models.game_state import GameState, Message, MessageRole
from agentic_rpg.state.manager import StateManager
from agentic_rpg.tools.registry import build_all_tools

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# ConnectionHub — manages active WebSocket connections keyed by session ID
# ---------------------------------------------------------------------------


class ConnectionHub:
    """Manages active WebSocket connections, one per session."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    def register(self, session_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket for a session, replacing any existing one."""
        self._connections[session_id] = websocket

    def unregister(self, session_id: str) -> None:
        """Remove a session's WebSocket. No-op if not present."""
        self._connections.pop(session_id, None)

    def get(self, session_id: str) -> WebSocket | None:
        """Get the WebSocket for a session, or None."""
        return self._connections.get(session_id)

    async def send_json(self, session_id: str, message: dict) -> None:
        """Send a JSON message to a session's WebSocket. No-op if not connected."""
        ws = self._connections.get(session_id)
        if ws is not None:
            await ws.send_json(message)

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Module-level hub instance
hub = ConnectionHub()


def _make_message(msg_type: str, data: dict) -> dict:
    """Build a WebSocket message envelope."""
    return {
        "type": msg_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_tools_and_model(
    game_state: GameState, event_bus: EventBus
) -> tuple[list[Any], Any]:
    """Return tools and chat model for building the agent graph.

    This is a thin helper that the WebSocket handler calls.
    It is separated out so tests can easily patch it.
    """
    # Lazy imports to avoid circular dependency issues
    from agentic_rpg.llm.client import create_chat_model

    tools = build_all_tools(game_state, event_bus)
    model = create_chat_model()
    return tools, model


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/api/v1/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """Handle a WebSocket connection for a game session."""
    await websocket.accept()

    # -- Validate player ID (header or query param fallback for browser WebSocket) --
    player_id_raw = websocket.headers.get("x-player-id") or websocket.query_params.get("player_id")
    if not player_id_raw:
        await websocket.send_json(
            _make_message("error", {"code": "missing_player_id", "message": "Missing X-Player-ID header"})
        )
        await websocket.close()
        return

    try:
        player_id = UUID(player_id_raw)
    except ValueError:
        await websocket.send_json(
            _make_message("error", {"code": "invalid_player_id", "message": "Invalid X-Player-ID header"})
        )
        await websocket.close()
        return

    # -- Validate session exists --
    pool = websocket.app.state.db_pool
    state_manager = StateManager(pool)
    game_state = await state_manager.load_game_state(UUID(session_id))

    if game_state is None:
        await websocket.send_json(
            _make_message("error", {"code": "session_not_found", "message": "Session not found"})
        )
        await websocket.close()
        return

    # -- Register connection and send connected message --
    hub.register(session_id, websocket)

    connected_data = {
        "session_id": str(session_id),
        "game_state": json.loads(game_state.model_dump_json()),
    }
    try:
        await websocket.send_json(_make_message("connected", connected_data))
    except WebSocketDisconnect:
        hub.unregister(session_id)
        return

    # -- Message loop --
    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            # Parse JSON
            try:
                message = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                await websocket.send_json(
                    _make_message("error", {"code": "invalid_message", "message": "Invalid JSON"})
                )
                continue

            msg_type = message.get("type")
            msg_data = message.get("data", {})

            if msg_type == "pong":
                # Heartbeat response — silently accept
                continue

            elif msg_type == "player_action":
                try:
                    action = PlayerActionData.model_validate(msg_data)
                except (ValidationError, Exception):
                    await websocket.send_json(
                        _make_message("error", {"code": "invalid_request", "message": "Missing text field"})
                    )
                    continue
                text = action.text.strip()
                if not text:
                    await websocket.send_json(
                        _make_message("error", {"code": "invalid_request", "message": "Missing text field"})
                    )
                    continue

                # Run the agent with full game context
                try:
                    event_bus = EventBus()
                    tools, model = get_tools_and_model(game_state, event_bus)
                    context = assemble_context(game_state, text)
                    graph = build_agent_graph(tools, model)
                    result = await graph.ainvoke({"messages": context["messages"]})
                    agent_text = result["messages"][-1].content

                    # Persist conversation history
                    now = datetime.now(timezone.utc)
                    game_state.conversation.history.append(
                        Message(role=MessageRole.player, content=text, timestamp=now)
                    )
                    game_state.conversation.history.append(
                        Message(role=MessageRole.agent, content=agent_text, timestamp=now)
                    )

                    # Save updated game state (tools may have mutated it)
                    await state_manager.save_game_state(game_state)

                    # Send agent response
                    await websocket.send_json(
                        _make_message("agent_response", {"text": agent_text, "is_complete": True})
                    )

                    # Send full state snapshot so frontend stays in sync
                    await websocket.send_json(
                        _make_message("state_snapshot", {
                            "game_state": json.loads(game_state.model_dump_json()),
                        })
                    )
                except Exception:
                    logger.exception("Agent error for session %s", session_id)
                    await websocket.send_json(
                        _make_message("error", {"code": "agent_error", "message": "Failed to process action"})
                    )

            else:
                await websocket.send_json(
                    _make_message("error", {"code": "invalid_message_type", "message": f"Unknown message type: {msg_type}"})
                )

    except WebSocketDisconnect:
        pass
    finally:
        hub.unregister(session_id)
