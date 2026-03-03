# Ralph B — Frontend Plan

## Overview

Build a minimal but functional Next.js chat UI for the agentic RPG. This runs in parallel with Ralph A (backend). The frontend needs to connect to the FastAPI backend via HTTP and WebSocket and provide a playable interface.

**Stack**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, WebSocket API.

**Key constraint**: Keep it simple and functional. No design system, no component library, just Tailwind utility classes. The goal is a working chat UI, not a polished product.

---

## Phase 7: Next.js Chat UI

### Goal
A single-page app where the user can create a game session and play through it via a chat interface, with a sidebar showing game state.

### Steps

1. Create `frontend/` directory with Next.js:
   - `npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --no-eslint`
   - Or manual setup if preferred

2. Create `frontend/Dockerfile`:
   - Node 20 alpine base
   - Copy project, npm install, npm run build, npm start
   - Expose port 3000

3. Update `docker-compose.yml` (coordinate with Ralph A):
   - `frontend` service: build from `frontend/`, port 3000, depends_on backend
   - Environment variable for backend URL (e.g., `NEXT_PUBLIC_API_URL=http://localhost:8080`)

4. Create TypeScript types manually (matching backend Pydantic models):
   - `frontend/types/game.ts`: GameState, Character, Inventory, Item, Location, World, StoryOutline, StoryBeat, Message, Session
   - `frontend/types/api.ts`: SessionCreateRequest, SessionCreateResponse, SessionSummary, PlayerAction, AgentResponse, StateUpdate, WSMessage
   - These should match the Pydantic models from `docs/specs/schema-registry.md` and `docs/models/api.py`

5. Create API client:
   - `frontend/lib/api.ts`: HTTP client for REST endpoints
     - `createSession(genre, character)` → POST /api/v1/sessions
     - `listSessions()` → GET /api/v1/sessions
     - `getSession(id)` → GET /api/v1/sessions/{id}
     - `deleteSession(id)` → DELETE /api/v1/sessions/{id}

6. Create WebSocket client:
   - `frontend/lib/websocket.ts`: WebSocket connection manager
     - `connect(sessionId)` — connects to ws://backend/api/v1/sessions/{id}/ws
     - `disconnect()` — clean close
     - `sendAction(text)` — sends player_action message
     - `onMessage(callback)` — registers handler for incoming messages
     - Auto-reconnect on disconnect (simple retry with backoff)
     - Parse incoming messages by type (agent_response, state_update, error, connected)

7. Create state management:
   - `frontend/lib/store.ts`: Simple React context or zustand store
     - `gameState`: Current GameState (character, inventory, location, story)
     - `messages`: Chat message history (player + agent messages)
     - `connectionStatus`: connected, connecting, disconnected
     - `currentSession`: Session metadata
     - Actions: setGameState, addMessage, updateFromStateEvent, setSession

8. Build pages:

   **Home Page** (`app/page.tsx`):
   - List existing sessions (cards with session name, last played date)
   - "New Game" button
   - Click session → navigate to /play/[sessionId]

   **New Game Page** (`app/new/page.tsx`):
   - Simple form: genre/setting (text input), character name, profession, background
   - Submit → POST /api/v1/sessions → redirect to /play/[sessionId]

   **Play Page** (`app/play/[sessionId]/page.tsx`):
   - Main layout: sidebar (left/right) + chat area (center)
   - Connects WebSocket on mount, disconnects on unmount

9. Build components:

   **ChatPanel** (`components/ChatPanel.tsx`):
   - Scrollable message list
   - Each message: player messages right-aligned (blue), agent messages left-aligned (gray)
   - Agent messages may stream in (append chunks until is_complete: true)
   - Text input at bottom with send button
   - Enter to send
   - Show "Agent is thinking..." indicator while waiting for response

   **CharacterPanel** (`components/CharacterPanel.tsx`):
   - Character name, profession
   - Stats display (health bar, energy bar, money)
   - Active status effects as tags/badges
   - Level and experience

   **InventoryPanel** (`components/InventoryPanel.tsx`):
   - List of items with name, type, quantity
   - Equipment slots showing what's equipped
   - Simple list layout, no drag-and-drop

   **LocationPanel** (`components/LocationPanel.tsx`):
   - Current location name and description
   - List of connected locations
   - NPCs present
   - Items present

   **StoryPanel** (`components/StoryPanel.tsx`):
   - Current story premise (collapsed/expandable)
   - Active beat summary
   - Progress indicator (beat X of Y)

   **Sidebar** (`components/Sidebar.tsx`):
   - Tabs or accordion: Character | Inventory | Location | Story
   - Renders the appropriate panel

10. Wire up state updates:
    - When WebSocket receives `state_update` messages, update the game state in the store
    - When WebSocket receives `connected` message, initialize game state from payload
    - When WebSocket receives `agent_response` chunks, append to current agent message
    - When agent response is complete (is_complete: true), finalize the message

11. Basic styling with Tailwind:
    - Dark theme (gray-900 background, gray-100 text)
    - Fixed sidebar width, flexible chat area
    - Mobile-friendly enough to not break (but not a priority)
    - Monospace font for game text (gives it an RPG feel)

### Definition of Done
- `docker compose up` starts frontend on port 3000
- Home page loads, shows session list
- Can create a new game session
- Play page connects WebSocket, shows chat UI
- Can type player actions and see agent responses stream in
- Sidebar shows character stats, inventory, location
- State updates reflected in sidebar when agent modifies game state

### Notes for Ralph

- Reference `docs/specs/frontend.md` for component details
- Reference `docs/specs/api-layer.md` for all endpoint contracts and WebSocket message formats
- Reference `docs/specs/schema-registry.md` for all data model shapes
- The backend may not be fully ready when you start — build against the spec, not the live API
- Use `NEXT_PUBLIC_API_URL` env var for backend URL (defaults to http://localhost:8080)
- For WebSocket URL, derive from API URL (replace http with ws)
- Keep components simple — no fancy animations, no component libraries
- Tailwind utility classes only, no custom CSS files
- TypeScript strict mode is fine but don't over-type — `any` is acceptable for speed
- Test manually by running the frontend and checking the UI works
