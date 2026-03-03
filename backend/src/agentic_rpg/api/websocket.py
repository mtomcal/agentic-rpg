"""WebSocket endpoint and ConnectionHub for real-time game communication."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agentic_rpg.agent.graph import build_agent_graph
from agentic_rpg.state.manager import StateManager

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


def get_tools_and_model() -> tuple[list[Any], Any]:
    """Return tools and chat model for building the agent graph.

    This is a thin helper that the WebSocket handler calls.
    It is separated out so tests can easily patch it.
    """
    # Lazy imports to avoid circular dependency issues
    from agentic_rpg.llm.client import create_chat_model

    model = create_chat_model()
    return [], model


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/api/v1/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """Handle a WebSocket connection for a game session."""
    await websocket.accept()

    # -- Validate player ID header --
    player_id_raw = websocket.headers.get("x-player-id")
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
    char = game_state.character
    loc_id = game_state.world.current_location_id
    loc = game_state.world.locations.get(loc_id)

    connected_data = {
        "session_id": str(session_id),
        "character": {
            "name": char.name,
            "profession": char.profession,
            "level": char.level,
        },
        "location": {
            "id": loc_id,
            "name": loc.name if loc else loc_id,
            "description": loc.description if loc else "",
        },
    }
    await websocket.send_json(_make_message("connected", connected_data))

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
                text = msg_data.get("text") if isinstance(msg_data, dict) else None
                if not text:
                    await websocket.send_json(
                        _make_message("error", {"code": "invalid_request", "message": "Missing text field"})
                    )
                    continue

                # Run the agent
                try:
                    tools, model = get_tools_and_model()
                    graph = build_agent_graph(tools, model)
                    result = await graph.ainvoke({"messages": [{"role": "user", "content": text}]})
                    agent_text = result["messages"][-1].content
                    await websocket.send_json(
                        _make_message("agent_response", {"text": agent_text, "is_complete": True})
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
