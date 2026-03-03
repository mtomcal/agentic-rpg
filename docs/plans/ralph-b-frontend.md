# Ralph B — Frontend Plan

## Overview

Build a minimal but functional Next.js chat UI for the agentic RPG. This runs in parallel with Ralph A (backend). The frontend needs to connect to the FastAPI backend via HTTP and WebSocket and provide a playable interface.

**Stack**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, WebSocket API.

**Key constraint**: Keep it simple and functional. No design system, no component library, just Tailwind utility classes. The goal is a working chat UI, not a polished product.

**Key constraint**: Check off items in this checklist as you complete them (edit this file). If stuck on something, skip it and move on — velocity matters.

---

## Phase 7: Next.js Chat UI

### Goal
A single-page app where the user can create a game session and play through it via a chat interface, with a sidebar showing game state.

### Checklist

#### Project Setup
- [x] Create `frontend/` directory with Next.js App Router
- [x] TypeScript enabled
- [x] Tailwind CSS configured
- [x] Verify `npm run dev` starts on port 3000
- [x] Verify `npm run build` succeeds

#### Docker Setup
- [ ] Create `frontend/Dockerfile` (Node 20 alpine, npm install, npm run build, npm start)
- [ ] `.dockerignore` with node_modules, .next, .git
- [ ] Add `frontend` service to `docker-compose.yml`:
  - Build from `frontend/`
  - Port 3000:3000
  - depends_on: backend
  - Environment: `NEXT_PUBLIC_API_URL=http://localhost:8080`
  - Environment: `NEXT_PUBLIC_WS_URL=ws://localhost:8080`
- [ ] `docker compose build frontend` succeeds
- [ ] `docker compose up frontend` starts and serves on port 3000

#### TypeScript Types (`types/`)
- [x] `types/game.ts`: `Character` interface — id, name, profession, background, stats, status_effects, level, experience, location_id
- [x] `types/game.ts`: `StatusEffect` interface — name, duration, description
- [x] `types/game.ts`: `Item` interface — id, name, description, item_type, quantity, properties
- [x] `types/game.ts`: `Inventory` interface — items, equipment, capacity
- [x] `types/game.ts`: `Location` interface — id, name, description, connections, npcs_present, items_present, visited
- [x] `types/game.ts`: `World` interface — locations, current_location_id, discovered_locations, world_flags
- [x] `types/game.ts`: `StoryBeat` interface — summary, location, trigger_conditions, key_elements, player_objectives, possible_outcomes, flexibility, status
- [x] `types/game.ts`: `StoryOutline` interface — premise, setting, beats
- [x] `types/game.ts`: `StoryState` interface — outline, active_beat_index, summary, adaptation_history
- [x] `types/game.ts`: `Message` interface — role, content, timestamp, metadata
- [x] `types/game.ts`: `Conversation` interface — history, window_size, summary
- [x] `types/game.ts`: `Session` interface — session_id, player_id, created_at, updated_at, schema_version, status
- [x] `types/game.ts`: `GameState` interface — session, character, inventory, world, story, conversation, recent_events
- [x] `types/api.ts`: `SessionCreateRequest` interface — genre, character: { name, profession, background }
- [x] `types/api.ts`: `SessionCreateResponse` interface — session_id, game_state
- [x] `types/api.ts`: `SessionSummary` interface — session_id, status, character_name, created_at, updated_at
- [x] `types/api.ts`: `SessionListResponse` interface — sessions: SessionSummary[]
- [x] `types/api.ts`: `WSMessage` interface — type, data, timestamp
- [x] `types/api.ts`: `PlayerActionMessage` — type: "player_action", data: { text }
- [x] `types/api.ts`: `AgentResponseMessage` — type: "agent_response", data: { text, is_complete }
- [x] `types/api.ts`: `StateUpdateMessage` — type: "state_update", data: { event_type, changes }
- [x] `types/api.ts`: `ConnectedMessage` — type: "connected", data: { session_id, game_state }
- [x] `types/api.ts`: `ErrorMessage` — type: "error", data: { code, message }

#### API Client (`lib/api.ts`)
- [x] `getApiUrl()` helper — reads NEXT_PUBLIC_API_URL, defaults to http://localhost:8080
- [x] `createSession(genre: string, character: { name, profession, background })` → POST /api/v1/sessions → SessionCreateResponse
- [x] `listSessions()` → GET /api/v1/sessions → SessionListResponse
- [x] `getSession(sessionId: string)` → GET /api/v1/sessions/{id} → { game_state: GameState }
- [x] `deleteSession(sessionId: string)` → DELETE /api/v1/sessions/{id} → { success: boolean }
- [x] Error handling: throw on non-2xx responses with message from body

#### WebSocket Client (`lib/websocket.ts`)
- [x] `GameWebSocket` class or module
- [x] `connect(sessionId: string)` — opens WebSocket to ws://host/api/v1/sessions/{id}/ws
- [x] `disconnect()` — closes WebSocket cleanly
- [x] `sendAction(text: string)` — sends { type: "player_action", data: { text }, timestamp: ISO }
- [x] `onConnected(callback)` — register handler for "connected" messages
- [x] `onAgentResponse(callback)` — register handler for "agent_response" messages
- [x] `onStateUpdate(callback)` — register handler for "state_update" messages
- [x] `onError(callback)` — register handler for "error" messages
- [x] `onClose(callback)` — register handler for connection close
- [x] Auto-reconnect: on unexpected close, retry after 1s, 2s, 4s (up to 30s)
- [x] `getStatus()` — returns "connecting" | "connected" | "disconnected"

#### State Management (`lib/store.ts`)
- [x] Choose approach: React Context + useReducer OR zustand (either is fine)
- [x] State shape: `{ gameState: GameState | null, messages: ChatMessage[], connectionStatus, currentSessionId, isAgentThinking }`
- [x] `ChatMessage` type: `{ id: string, role: "player" | "agent" | "system", content: string, timestamp: string, isStreaming: boolean }`
- [x] Action: `setGameState(state: GameState)`
- [x] Action: `addPlayerMessage(text: string)`
- [x] Action: `startAgentMessage()` — creates new agent message with isStreaming: true
- [x] Action: `appendAgentChunk(text: string)` — appends to current streaming message
- [x] Action: `finalizeAgentMessage()` — sets isStreaming: false
- [x] Action: `updateFromStateEvent(event)` — apply state_update to gameState
- [x] Action: `setConnectionStatus(status)`
- [x] Action: `setCurrentSessionId(id)`
- [x] Action: `setAgentThinking(thinking: boolean)`
- [x] Action: `clearMessages()`

#### Home Page (`app/page.tsx`)
- [ ] Fetch sessions on mount via `listSessions()`
- [ ] Display session cards: character name, genre/setting, last played date, status
- [ ] "New Game" button → navigates to /new
- [ ] Click session card → navigates to /play/[sessionId]
- [ ] Empty state: "No sessions yet. Start a new game!"
- [ ] Loading state while fetching
- [ ] Error state if API unreachable
- [ ] Delete button on each session card (with confirmation)

#### New Game Page (`app/new/page.tsx`)
- [ ] Form fields: genre/setting (text input), character name (text input), profession (text input), background (textarea)
- [ ] All fields required
- [ ] Submit button: "Start Adventure"
- [ ] On submit: call `createSession()`, on success redirect to /play/[sessionId]
- [ ] Loading state while creating
- [ ] Error display if creation fails
- [ ] Back button to home

#### Play Page (`app/play/[sessionId]/page.tsx`)
- [ ] Layout: sidebar (right side, ~320px) + chat area (remaining width)
- [ ] On mount: connect WebSocket to session
- [ ] On unmount: disconnect WebSocket
- [ ] On "connected" message: initialize gameState in store
- [ ] On "agent_response" message: stream into chat
- [ ] On "state_update" message: update gameState in store
- [ ] On "error" message: display error in chat
- [ ] Connection status indicator (green dot = connected, yellow = connecting, red = disconnected)
- [ ] Back button to home

#### ChatPanel Component (`components/ChatPanel.tsx`)
- [x] Scrollable message list (flex-col, overflow-y-auto)
- [x] Player messages: right-aligned, blue/indigo background, rounded
- [x] Agent messages: left-aligned, gray/dark background, rounded, monospace font
- [x] System messages: centered, muted color, italic
- [x] Auto-scroll to bottom on new messages
- [x] Streaming indicator: blinking cursor or "..." while agent message is streaming
- [x] "Agent is thinking..." indicator while waiting for first chunk
- [x] Text input at bottom: full width, with send button
- [x] Enter key sends message (Shift+Enter for newline)
- [x] Input disabled while agent is responding
- [x] Input auto-focuses on page load
- [x] Empty state: "Start your adventure by typing an action..."

#### CharacterPanel Component (`components/CharacterPanel.tsx`)
- [x] Character name (large text)
- [x] Profession and level: "Level 1 Knight"
- [x] Health bar: colored bar (green > 50%, yellow > 25%, red <= 25%), shows current/max
- [x] Energy bar: blue colored bar, shows current/max
- [x] Money display
- [x] Status effects: list of tags/badges with name and remaining duration
- [x] Experience: "XP: 0 / 100" or similar
- [x] Handles missing/null game state gracefully (loading placeholder)

#### InventoryPanel Component (`components/InventoryPanel.tsx`)
- [x] Item list: name, type (colored badge), quantity
- [x] Equipment section: slot name → equipped item name (or "Empty")
- [x] Empty inventory message: "Your inventory is empty"
- [x] Item type color coding: weapon=red, armor=blue, consumable=green, key=yellow, misc=gray

#### LocationPanel Component (`components/LocationPanel.tsx`)
- [ ] Current location name (header)
- [ ] Location description (paragraph)
- [ ] "Connected locations" list with names
- [ ] "NPCs here" list (if any)
- [ ] "Items here" list (if any)
- [ ] Handles missing location data gracefully

#### StoryPanel Component (`components/StoryPanel.tsx`)
- [ ] Story premise (expandable/collapsible, default collapsed)
- [ ] Current beat summary (always visible)
- [ ] Progress: "Chapter X of Y" or progress bar
- [ ] Beat status indicator: active (pulsing dot), resolved (checkmark), skipped (dash)
- [ ] Beat list: shows all beats with their status (scrollable if many)

#### Sidebar Component (`components/Sidebar.tsx`)
- [ ] Tab bar: Character | Inventory | Location | Story
- [ ] Active tab highlighted
- [ ] Renders the selected panel component
- [ ] Default tab: Character
- [ ] Scrollable panel content area
- [ ] Fixed width, full height

#### Layout & Styling
- [x] `app/layout.tsx`: dark theme base styles (bg-gray-900, text-gray-100)
- [x] Global font: monospace or system monospace for game feel
- [x] Responsive: doesn't break on mobile (sidebar collapses or hides)
- [x] Loading spinner component for reuse
- [x] Consistent padding and spacing

#### WebSocket ↔ Store Integration
- [ ] "connected" message → `setGameState(data.game_state)`, `setConnectionStatus("connected")`
- [ ] "agent_response" with is_complete=false → `appendAgentChunk(data.text)`
- [ ] "agent_response" with is_complete=true → `finalizeAgentMessage()`, `setAgentThinking(false)`
- [ ] "state_update" → `updateFromStateEvent(data)` (update character/inventory/location/story as appropriate)
- [ ] "error" → display error message in chat as system message
- [ ] WebSocket close → `setConnectionStatus("disconnected")`
- [ ] Player sends action → `addPlayerMessage(text)`, `setAgentThinking(true)`, `startAgentMessage()`, `ws.sendAction(text)`

#### Docker Integration
- [ ] `docker compose build` builds frontend successfully
- [ ] `docker compose up` starts all 3 services (postgres, backend, frontend)
- [ ] Frontend accessible at http://localhost:3000
- [ ] Frontend can reach backend API (CORS configured on backend)
- [ ] WebSocket connection works through Docker networking

#### End-to-End Verification (manual)
- [ ] Open http://localhost:3000 — home page loads
- [ ] Click "New Game" — form appears
- [ ] Fill form, submit — redirected to play page
- [ ] Play page: WebSocket connects, "connected" message received, game state populates sidebar
- [ ] Type an action, press Enter — message appears in chat
- [ ] Agent response streams in (or error if backend not ready — that's OK)
- [ ] Sidebar tabs switch correctly
- [ ] Character panel shows stats
- [ ] Inventory panel shows items
- [ ] Location panel shows current location
- [ ] Story panel shows outline info

#### Phase 7 Wrap-up
- [ ] All checklist items above completed or intentionally skipped
- [ ] `npm run build` succeeds with no errors
- [ ] `docker compose build frontend` succeeds
- [ ] Commit: `git add -A && git commit -m "phase 7: Next.js chat UI"`

---

## Notes for Ralph

- Reference `docs/specs/frontend.md` for component details
- Reference `docs/specs/api-layer.md` for all endpoint contracts and WebSocket message formats
- Reference `docs/specs/schema-registry.md` for all data model shapes
- The backend may not be fully ready when you start — build against the spec, not the live API
- Use `NEXT_PUBLIC_API_URL` env var for backend URL (defaults to http://localhost:8080)
- For WebSocket URL, use `NEXT_PUBLIC_WS_URL` or derive from API URL (replace http with ws)
- Keep components simple — no fancy animations, no component libraries
- Tailwind utility classes only, no custom CSS files
- TypeScript strict mode is fine but don't over-type — `any` is acceptable for speed
- Test manually by running the frontend and checking the UI works
- Check off items in this checklist as you complete them (edit this file)
- If stuck on something for more than a few minutes, skip it and move on — velocity matters
