# Technology Choice: WebSockets

## Decision

Use WebSockets for real-time communication between the frontend and backend during gameplay.

## Rationale

- **Bidirectional**: Both client and server can send messages at any time. Needed for pushing state updates and streaming agent responses.
- **Low overhead**: After the initial handshake, messages are lightweight framed data. No HTTP header overhead per message.
- **Simple**: The WebSocket API is native in browsers and well-supported in FastAPI/Starlette. No extra libraries needed on the frontend.
- **Streaming**: Agent responses stream token-by-token. WebSocket is the natural fit for pushing text chunks as they arrive.
- **Why not SSE**: Server-Sent Events are server->client only. We need client->server for player actions during an active connection. SSE + HTTP POST would work but is more complex than a single WebSocket.
- **Why not polling**: Wasteful and high-latency. The game needs sub-second updates for streaming text.

## Protocol Design

See [API Layer](../specs/api-layer.md) for the full message format specification. Summary:

### Message Envelope

All messages are JSON:
```json
{
  "type": "message_type",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Client -> Server

| Type | Purpose |
|------|---------|
| `player_action` | Player sends a text command |
| `pong` | Response to server heartbeat |

### Server -> Client

| Type | Purpose |
|------|---------|
| `connected` | Initial connection confirmation + state summary |
| `agent_response` | Narrative text (streamed in chunks) |
| `state_update` | Game state change notification |
| `error` | Error message |
| `ping` | Heartbeat (client must respond with pong) |

## Connection Lifecycle

1. Client opens WebSocket to `/api/v1/sessions/:id/ws`
2. Server validates session, registers connection in the hub
3. Server sends `connected` message
4. Normal message exchange begins
5. Server sends `ping` every 30 seconds
6. Client must respond with `pong` within 10 seconds or the connection is closed
7. On disconnect, client auto-reconnects with exponential backoff (1s, 2s, 4s, 8s, max 30s)
8. On reconnect, client re-fetches full state via HTTP to re-sync

## Server-Side Architecture

### FastAPI WebSocket Endpoint

WebSocket connections are handled by FastAPI's WebSocket support (built on Starlette):

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/api/v1/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    hub.register(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(session_id, data)
    except WebSocketDisconnect:
        hub.unregister(session_id)
```

### WebSocket Hub

A central async hub manages all active WebSocket connections:

- **Register**: Add a new connection (keyed by session ID)
- **Unregister**: Remove a connection
- **Send**: Send a message to a specific session's connection
- **Broadcast**: Not needed (no multiplayer), but the hub pattern supports it if needed later

Each session has at most one active WebSocket connection. If a new connection opens for a session that already has one, the old connection is closed.

```python
class ConnectionHub:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    def register(self, session_id: str, websocket: WebSocket):
        if session_id in self._connections:
            # Close existing connection
            asyncio.create_task(self._connections[session_id].close())
        self._connections[session_id] = websocket

    def unregister(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send(self, session_id: str, message: dict):
        if ws := self._connections.get(session_id):
            await ws.send_json(message)
```

### Async Task Model

Each WebSocket connection uses **asyncio tasks** instead of goroutines:

- **Read path**: The `while True` loop in the endpoint reads messages from the client and dispatches to the agent
- **Write path**: The hub's `send` method writes messages to the client. Since FastAPI WebSocket operations are async, writes don't block reads.
- **Heartbeat task**: An `asyncio.create_task` runs the ping/pong loop for each connection

```python
async def heartbeat(session_id: str, websocket: WebSocket):
    while True:
        await asyncio.sleep(30)
        await websocket.send_json({"type": "ping"})
```

The asyncio event loop handles concurrency — no thread/goroutine management needed. `asyncio.create_task` spawns concurrent operations within a single connection.

## Frontend Implementation

Use the native browser `WebSocket` API. A thin wrapper class handles:

- Connection/reconnection logic
- Message parsing and type-safe dispatch (switch on `type` field)
- Heartbeat handling
- State: `connecting`, `connected`, `reconnecting`, `disconnected`

No Socket.IO or other libraries needed.

## Future Extensions

- **Binary messages**: Use MessagePack or Protobuf for smaller payloads if JSON becomes a bottleneck
- **Compression**: WebSocket per-message compression (`permessage-deflate`) for large payloads
- **Multiple connections per session**: If we add spectator mode or collaborative play
