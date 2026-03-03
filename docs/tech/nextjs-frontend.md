# Technology Choice: Next.js Frontend

## Decision

Use Next.js with TypeScript for the frontend client.

## Rationale

- **Industry standard**: Next.js is the default React framework. Well-understood by AI assistants and human developers alike.
- **TypeScript**: Full type safety, especially valuable when types are generated from backend Pydantic models.
- **Not a learning goal**: The frontend is a means to an end. Use the most conventional, well-supported stack so development is fast and predictable.
- **SSR optional**: Next.js supports server-side rendering, but we may not need it initially. It's there if we want it.

## What We're Using

- **Next.js** (App Router) — framework
- **TypeScript** — language
- **Tailwind CSS** — styling (utility-first, fast to build with)
- **Zustand** — lightweight state management
- **Native WebSocket API** — no socket library needed for simple use
- **Generated types** — TypeScript interfaces generated from Pydantic models (see [Pydantic Models](pydantic-models.md))

## What We're NOT Using

- **Component libraries** (shadcn, Material UI, Chakra) — Tailwind is sufficient, keep it lean
- **Redux / MobX** — overkill for this use case
- **Socket.IO** — native WebSocket is simpler and we control the protocol
- **GraphQL** — REST + WebSocket is simpler for our needs
- **Storybook** — not needed for a solo project

## Project Structure

```
frontend/
  src/
    app/
      page.tsx              # Home screen (session list)
      game/[id]/page.tsx    # Game screen
      new/page.tsx          # Character creation
      layout.tsx            # Root layout
    components/
      narrative-panel.tsx   # Main chat/narrative display
      character-panel.tsx   # Character stats sidebar
      inventory-panel.tsx   # Inventory display
      location-panel.tsx    # Current location info
      player-input.tsx      # Text input for player actions
      session-list.tsx      # List of saved sessions
      character-form.tsx    # Character creation form
    lib/
      api.ts                # HTTP API client
      websocket.ts          # WebSocket connection manager
      store.ts              # Zustand store
    generated/
      ...                   # Generated TypeScript types from Pydantic models
  tailwind.config.ts
  tsconfig.json
  next.config.ts
  package.json
```

## Key Patterns

### WebSocket Manager

A simple class that manages the WebSocket connection lifecycle:
- Connect/disconnect
- Auto-reconnect with exponential backoff
- Message parsing and type-safe dispatch
- Heartbeat handling

### State Store

Zustand store with slices for:
- `gameState`: Mirrored from server, updated by WebSocket events
- `uiState`: Panel visibility, input state, etc.
- `connectionState`: WebSocket status

### Type Safety

All API responses and WebSocket messages are typed using the generated TypeScript interfaces. No `any` types at the boundaries.

Types are generated from the backend's Pydantic models using `pydantic-to-typescript` or `datamodel-code-generator`. The generation runs as part of the build pipeline and CI verifies no drift between the Python models and the TypeScript types.

## Build and Run

```bash
# Development
npm run dev

# Build
npm run build

# Test
npm run test

# Regenerate types from Pydantic models
npm run generate-types
```
